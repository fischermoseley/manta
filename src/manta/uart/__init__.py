from amaranth import *
from manta.utils import *
from manta.uart.receiver import UARTReceiver
from manta.uart.receive_bridge import ReceiveBridge
from manta.uart.transmitter import UARTTransmitter
from manta.uart.transmit_bridge import TransmitBridge
from serial import Serial


class UARTInterface(Elaboratable):
    """
    A module for communicating with Manta over UART.

    Provides methods for generating synthesizable logic for the FPGA, as well
    as methods for reading and writing to memory by the host.

    More information available in the online documentation at:
    https://fischermoseley.github.io/manta/uart_interface/
    """

    def __init__(self, port, baudrate, clock_freq, chunk_size=256):
        self._port = port
        self._baudrate = baudrate
        self._clock_freq = clock_freq
        self._chunk_size = chunk_size
        self._clocks_per_baud = int(self._clock_freq // self._baudrate)
        self._check_config()

        # Top-Level Ports
        self.rx = Signal()
        self.tx = Signal()

        self.bus_o = Signal(InternalBus())
        self.bus_i = Signal(InternalBus())

    @classmethod
    def from_config(cls, config):
        port = config.get("port")
        clock_freq = config.get("clock_freq")
        baudrate = config.get("baudrate")

        # Warn if unrecognized options have been given
        recognized_options = ["port", "clock_freq", "baudrate", "chunk_size"]
        for option in config:
            if option not in recognized_options:
                warn(
                    f"Ignoring unrecognized option '{option}' in UART interface config."
                )

        if "chunk_size" in config:
            return cls(port, baudrate, clock_freq, config["chunk_size"])

        else:
            return cls(port, baudrate, clock_freq)

    def _check_config(self):
        # Ensure a serial port has been given
        if self._port is None:
            raise ValueError("No serial port provided to UART interface.")

        # Ensure clock frequency is provided and positive
        if self._clock_freq is None:
            raise ValueError("No clock frequency provided to UART interface.")

        if self._clock_freq <= 0:
            raise ValueError("Non-positive clock frequency provided to UART interface.")

        # Check that baudrate is provided and positive
        if self._baudrate is None:
            raise ValueError("No baudrate provided to UART interface.")

        if self._baudrate <= 0:
            raise ValueError("Non-positive baudrate provided to UART interface.")

        # Confirm the actual baudrate is within 5% of the target baudrate
        actual_baudrate = self._clock_freq / self._clocks_per_baud
        error = 100 * abs(actual_baudrate - self._baudrate) / self._baudrate

        if error > 5:
            raise ValueError(
                "UART interface is unable to match targeted baudrate with specified clock frequency."
            )

    def _get_serial_device(self):
        """
        Return an open PySerial serial device if one exists, otherwise, open
        one and return it.
        """

        # Check if we've already opened a device
        if hasattr(self, "_serial_device"):
            return self._serial_device

        if self._port != "auto":
            self._serial_device = Serial(self._port, self._baudrate, timeout=1)
            return self._serial_device

        # Try to autodetect which port to use based on the PID/VID of the device attached.
        # This looks for the PID/VID of the FT2232, the primary chip used on the icestick
        # and Digilent dev boards. However, folks will likely want to connect other things
        # in the future, so in the future we'll probably want to look for other chips as
        # well.

        # The FT2232 exposes two serial ports - and for whatever reason it usually has the
        # 0th device used for JTAG programming, and the 1st used for UART. So we'll grab
        # the 1st.

        import serial.tools.list_ports

        ports = []
        for port in serial.tools.list_ports.comports():
            if (port.vid == 0x403) and (port.pid == 0x6010):
                ports.append(port)

        if len(ports) != 2:
            raise ValueError(
                f"Expected to see two serial ports for FT2232 device, but instead see {len(ports)}."
            )

        if ports[0].serial_number != ports[1].serial_number:
            raise ValueError(
                f"Serial numbers should be the same on both FT2232 ports - probably somehow grabbed ports on two different devices."
            )

        if ports[0].location > ports[1].location:
            chosen_port = ports[0].device

        else:
            chosen_port = ports[1].device

        self._serial_device = Serial(chosen_port, self._baudrate, timeout=1)
        return self._serial_device

    def get_top_level_ports(self):
        """
        Return the Amaranth signals that should be included as ports in the
        top-level Manta module.
        """
        return [self.rx, self.tx]

    def read(self, addrs):
        """
        Read the data stored in a set of address on Manta's internal memory.
        Addresses must be specified as either integers or a list of integers.
        """

        # Handle a single integer address
        if isinstance(addrs, int):
            return self.read([addrs])[0]

        # Make sure all list elements are integers
        if not all(isinstance(a, int) for a in addrs):
            raise TypeError("Read address must be an integer or list of integers.")

        # Send read requests in chunks, and read bytes after each.
        # The input buffer exposed by the OS on most hosts isn't terribly deep,
        # so sending in chunks (instead of all at once) prevents the OS's input
        # buffer from overflowing and dropping bytes, as the FPGA will send
        # responses instantly after it's received a request.

        ser = self._get_serial_device()
        addr_chunks = split_into_chunks(addrs, self._chunk_size)
        datas = []

        for addr_chunk in addr_chunks:
            # Encode addrs into read requests
            bytes_out = "".join([f"R{a:04X}\r\n" for a in addr_chunk])

            # Add a \n after every 32 packets, see:
            # https://github.com/fischermoseley/manta/issues/18
            bytes_out = "\n".join(split_into_chunks(bytes_out, 7 * 32))

            ser.write(bytes_out.encode("ascii"))

            # Read responses have the same length as read requests
            bytes_expected = 7 * len(addr_chunk)
            bytes_in = ser.read(bytes_expected)

            if len(bytes_in) != bytes_expected:
                raise ValueError(
                    f"Only got {len(bytes_in)} out of {bytes_expected} bytes."
                )

            # Split received bytes into individual responses and decode
            responses = split_into_chunks(bytes_in, 7)
            data_chunk = [self._decode_read_response(r) for r in responses]
            datas += data_chunk

        return datas

    def write(self, addrs, datas):
        """
        Write the provided data into the provided addresses in Manta's internal
        memory. Addresses and data must be specified as either integers or a
        list of integers.
        """

        # Handle a single integer address and data
        if isinstance(addrs, int) and isinstance(datas, int):
            return self.write([addrs], [datas])

        # Make sure address and datas are all integers
        if not isinstance(addrs, list) or not isinstance(datas, list):
            raise TypeError(
                "Write addresses and data must be an integer or list of integers."
            )

        if not all(isinstance(a, int) for a in addrs):
            raise TypeError("Write addresses must be all be integers.")

        if not all(isinstance(d, int) for d in datas):
            raise TypeError("Write data must all be integers.")

        # Since the FPGA doesn't issue any responses to write requests, we
        # the host's input buffer isn't written to, and we don't need to
        # send the data as chunks as the to avoid overflowing the input buffer.

        # Encode addrs and datas into write requests
        bytes_out = "".join([f"W{a:04X}{d:04X}\r\n" for a, d in zip(addrs, datas)])
        ser = self._get_serial_device()
        ser.write(bytes_out.encode("ascii"))

    def _decode_read_response(self, response_bytes):
        """
        Check that read response is formatted properly, and return the encoded
        data if so.
        """

        # Make sure response is not empty
        if response_bytes is None:
            raise ValueError("Unable to decode read response - no bytes received.")

        # Make sure response is properly encoded
        response_ascii = response_bytes.decode("ascii")

        if len(response_ascii) != 7:
            raise ValueError(
                "Unable to decode read response - wrong number of bytes received."
            )

        if response_ascii[0] != "D":
            raise ValueError("Unable to decode read response - incorrect preamble.")

        for i in range(1, 5):
            if response_ascii[i] not in "0123456789ABCDEF":
                raise ValueError("Unable to decode read response - invalid data byte.")

        if response_ascii[5] != "\r":
            raise ValueError("Unable to decode read response - incorrect EOL.")

        if response_ascii[6] != "\n":
            raise ValueError("Unable to decode read response - incorrect EOL.")

        return int(response_ascii[1:5], 16)

    def elaborate(self, platform):
        m = Module()

        m.submodules.uart_rx = uart_rx = UARTReceiver(self._clocks_per_baud)
        m.submodules.bridge_rx = bridge_rx = ReceiveBridge()
        m.submodules.bridge_tx = bridge_tx = TransmitBridge()
        m.submodules.uart_tx = uart_tx = UARTTransmitter(self._clocks_per_baud)

        m.d.comb += [
            # UART RX -> Internal Bus
            uart_rx.rx.eq(self.rx),
            bridge_rx.data_i.eq(uart_rx.data_o),
            bridge_rx.valid_i.eq(uart_rx.valid_o),
            self.bus_o.data.eq(bridge_rx.data_o),
            self.bus_o.addr.eq(bridge_rx.addr_o),
            self.bus_o.rw.eq(bridge_rx.rw_o),
            self.bus_o.valid.eq(bridge_rx.valid_o),
            # Internal Bus -> UART TX
            bridge_tx.data_i.eq(self.bus_i.data),
            bridge_tx.rw_i.eq(self.bus_i.rw),
            bridge_tx.valid_i.eq(self.bus_i.valid),
            uart_tx.data_i.eq(bridge_tx.data_o),
            uart_tx.start_i.eq(bridge_tx.start_o),
            bridge_tx.done_i.eq(uart_tx.done_o),
            self.tx.eq(uart_tx.tx),
        ]
        return m
