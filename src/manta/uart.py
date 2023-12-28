from amaranth import *
from amaranth.lib.data import ArrayLayout
from warnings import warn
from .utils import *
from serial import Serial


class UARTInterface(Elaboratable):
    def __init__(self, config):
        self.config = config
        self.check_config(self.config)

        self.port = config["port"]
        self.clock_freq = config["clock_freq"]
        self.baudrate = config["baudrate"]
        self.clocks_per_baud = int(self.clock_freq // self.baudrate)

        self.define_signals()

        # Set chunk_size, which is the max amount of bytes that the core will
        # dump to the OS driver at a time. Since the FPGA will return bytes
        # almost instantaneously, this prevents the OS's input buffer from
        # overflowing, and dropping bytes.
        self.chunk_size = 256  # in bytes
        if "chunk_size" in config:
            self.chunk_size = config["chunk_size"]

    def check_config(self, config):
        # Warn if unrecognized options have been given
        recognized_options = ["port", "clock_freq", "baudrate", "chunk_size"]
        for option in config:
            if option not in recognized_options:
                warn(
                    f"Ignoring unrecognized option '{option}' in UART interface config."
                )

        # Ensure a serial port has been given
        if "port" not in config:
            raise ValueError("No serial port provided to UART interface.")

        # Ensure clock frequency is provided and positive
        if "clock_freq" not in config:
            raise ValueError("No clock frequency provided to UART interface.")

        if config["clock_freq"] <= 0:
            raise ValueError("Non-positive clock frequency provided to UART interface.")

        # Check that baudrate is provided and positive
        if "baudrate" not in config:
            raise ValueError("No baudrate provided to UART interface.")

        if config["baudrate"] <= 0:
            raise ValueError("Non-positive baudrate provided to UART interface.")

        # Confirm the actual baudrate is within 5% of the target baudrate
        clock_freq = config["clock_freq"]
        baudrate = config["baudrate"]
        clocks_per_baud = clock_freq // baudrate
        actual_baudrate = clock_freq / clocks_per_baud
        error = 100 * abs(actual_baudrate - baudrate) / baudrate

        if error > 5:
            raise ValueError(
                "UART interface is unable to match targeted baudrate with specified clock frequency."
            )

    def get_serial_device(self):
        """
        Return an open PySerial serial device if one exists, otherwise, open one.
        """
        if hasattr(self, "serial_device"):
            return self.serial_device

        else:
            if self.port != "auto":
                self.serial_device = Serial(self.port, self.baudrate, timeout=1)
                return self.serial_device

            else:
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

                self.serial_device = Serial(chosen_port, self.baudrate, timeout=1)
                return self.serial_device

    def get_top_level_ports(self):
        return [self.rx, self.tx]

    def read(self, addrs):
        """
        Read the data stored in a set of address on Manta's internal memory. Addresses
        must be specified as either integers or a list of integers.
        """

        # Handle a single integer address
        if isinstance(addrs, int):
            return self.read([addrs])[0]

        # Make sure all list elements are integers
        if not all(isinstance(a, int) for a in addrs):
            raise ValueError("Read address must be an integer or list of integers.")

        # Send read requests, and get responses
        ser = self.get_serial_device()
        addr_chunks = split_into_chunks(addrs, self.chunk_size)
        datas = []

        for addr_chunk in addr_chunks:
            # Encode addrs into read requests
            bytes_out = b"".join([f"R{a:04X}\r\n".encode("ascii") for a in addr_chunk])
            ser.write(bytes_out)

            # Read responses have the same length as read requests
            bytes_in = ser.read(len(bytes_out))

            if len(bytes_in) != len(bytes_out):
                raise ValueError(
                    f"Only got {len(bytes_in)} out of {len(bytes_out)} bytes."
                )

            # Split received bytes into individual responses and decode
            responses = split_into_chunks(bytes_in, 7)
            data_chunk = [self.decode_read_response(r) for r in responses]
            datas += data_chunk

        return datas

    def write(self, addrs, datas):
        """
        Write the provided data into the provided addresses in Manta's internal memory.
        Addresses and data must be specified as either integers or a list of integers.
        """

        # Handle a single integer address and data
        if isinstance(addrs, int) and isinstance(datas, int):
            return self.write([addrs], [datas])

        # Make sure address and datas are all integers
        if not isinstance(addrs, list) or not isinstance(datas, list):
            raise ValueError(
                "Write addresses and data must be an integer or list of integers."
            )

        if not all(isinstance(a, int) for a in addrs):
            raise ValueError("Write addresses must be all be integers.")

        if not all(isinstance(d, int) for d in datas):
            raise ValueError("Write data must all be integers.")

        # I'm not sure if it's necessary to split outputs into chunks
        # I think the output buffer doesn't really drop stuff, just the input buffer

        # Encode addrs and datas into write requests
        bytes_out = "".join([f"W{a:04X}{d:04X}\r\n" for a, d in zip(addrs, datas)])
        bytes_out = bytes_out.encode("ascii")
        ser = self.get_serial_device()
        ser.write(bytes_out)

    def decode_read_response(self, response_bytes):
        """
        Check that read response is formatted properly, and extract the encoded data if so.
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

    def define_signals(self):
        self.rx = Signal()
        self.tx = Signal()

        self.addr_o = Signal(16)
        self.data_o = Signal(16)
        self.rw_o = Signal()
        self.valid_o = Signal()

        self.addr_i = Signal(16)
        self.data_i = Signal(16)
        self.rw_i = Signal()
        self.valid_i = Signal()

    def elaborate(self, platform):
        # fancy submoduling and such goes in here
        m = Module()

        m.submodules["uart_rx"] = uart_rx = UARTReceiver(self.clocks_per_baud)
        m.submodules["bridge_rx"] = bridge_rx = RecieveBridge()
        m.submodules["bridge_tx"] = bridge_tx = TransmitBridge()
        m.submodules["uart_tx"] = uart_tx = UARTTransmitter(self.clocks_per_baud)

        m.d.comb += [
            # UART RX -> Internal Bus
            uart_rx.rx.eq(self.rx),
            bridge_rx.data_i.eq(uart_rx.data_o),
            bridge_rx.valid_i.eq(uart_rx.valid_o),
            self.data_o.eq(bridge_rx.data_o),
            self.addr_o.eq(bridge_rx.addr_o),
            self.rw_o.eq(bridge_rx.rw_o),
            self.valid_o.eq(bridge_rx.valid_o),
            # Internal Bus -> UART TX
            bridge_tx.data_i.eq(self.data_i),
            bridge_tx.rw_i.eq(self.rw_i),
            bridge_tx.valid_i.eq(self.valid_i),
            uart_tx.data_i.eq(bridge_tx.data_o),
            uart_tx.start_i.eq(bridge_tx.start_o),
            bridge_tx.done_i.eq(uart_tx.done_o),
            self.tx.eq(uart_tx.tx),
        ]
        return m


class UARTReceiver(Elaboratable):
    def __init__(self, clocks_per_baud):
        self.clocks_per_baud = clocks_per_baud

        # Top-Level Ports
        self.rx = Signal()
        self.data_o = Signal(8, reset=0)
        self.valid_o = Signal(1, reset=0)

        # Internal Signals
        self.busy = Signal()
        self.bit_index = Signal(range(10))
        self.baud_counter = Signal(range(2 * clocks_per_baud))

        self.rx_d = Signal()
        self.rx_q = Signal()
        self.rx_q_prev = Signal()

    def elaborate(self, platform):
        m = Module()

        # Two Flip-Flop Synchronizer
        m.d.sync += [
            self.rx_d.eq(self.rx),
            self.rx_q.eq(self.rx_d),
            self.rx_q_prev.eq(self.rx_q),
        ]

        m.d.sync += self.valid_o.eq(0)

        with m.If(~self.busy):
            with m.If((~self.rx_q) & (self.rx_q_prev)):
                m.d.sync += self.busy.eq(1)
                m.d.sync += self.bit_index.eq(8)
                m.d.sync += self.baud_counter.eq(
                    self.clocks_per_baud + (self.clocks_per_baud // 2) - 2
                )

        with m.Else():
            with m.If(self.baud_counter == 0):
                with m.If(self.bit_index == 0):
                    m.d.sync += self.valid_o.eq(1)
                    m.d.sync += self.busy.eq(0)
                    m.d.sync += self.bit_index.eq(0)
                    m.d.sync += self.baud_counter.eq(0)

                with m.Else():
                    # m.d.sync += self.data_o.eq(Cat(self.rx_q, self.data_o[0:7]))
                    m.d.sync += self.data_o.eq(Cat(self.data_o[1:8], self.rx_q))
                    m.d.sync += self.bit_index.eq(self.bit_index - 1)
                    m.d.sync += self.baud_counter.eq(self.clocks_per_baud - 1)

            with m.Else():
                m.d.sync += self.baud_counter.eq(self.baud_counter - 1)

        return m


class RecieveBridge(Elaboratable):
    def __init__(self):
        # Top-Level Ports
        self.data_i = Signal(8)
        self.valid_i = Signal()

        self.addr_o = Signal(16, reset=0)
        self.data_o = Signal(16, reset=0)
        self.rw_o = Signal(1, reset=0)
        self.valid_o = Signal(1, reset=0)

        # State Machine
        self.IDLE_STATE = 0
        self.READ_STATE = 1
        self.WRITE_STATE = 2

        # Internal Signals
        self.buffer = Signal(ArrayLayout(4, 8), reset_less=True)
        self.state = Signal(2, reset=self.IDLE_STATE)
        self.byte_num = Signal(4, reset=0)
        self.is_eol = Signal()
        self.is_ascii_hex = Signal()
        self.from_ascii_hex = Signal(8)

    def drive_ascii_signals(self, m):
        # Decode 0-9
        with m.If((self.data_i >= 0x30) & (self.data_i <= 0x39)):
            m.d.comb += self.is_ascii_hex.eq(1)
            m.d.comb += self.from_ascii_hex.eq(self.data_i - 0x30)

        # Decode A-F
        with m.Elif((self.data_i >= 0x41) & (self.data_i <= 0x46)):
            m.d.comb += self.is_ascii_hex.eq(1)
            m.d.comb += self.from_ascii_hex.eq(self.data_i - 0x41 + 10)

        with m.Else():
            m.d.comb += self.is_ascii_hex.eq(0)
            m.d.comb += self.from_ascii_hex.eq(0)

        with m.If((self.data_i == ord("\r")) | (self.data_i == ord("\n"))):
            m.d.comb += self.is_eol.eq(1)

        with m.Else():
            m.d.comb += self.is_eol.eq(0)

    def drive_output_bus(self, m):
        with m.If(
            (self.state == self.READ_STATE) & (self.byte_num == 4) & (self.is_eol)
        ):
            m.d.comb += self.addr_o.eq(
                Cat(self.buffer[3], self.buffer[2], self.buffer[1], self.buffer[0])
            )
            m.d.comb += self.data_o.eq(0)
            m.d.comb += self.valid_o.eq(1)
            m.d.comb += self.rw_o.eq(0)

        with m.Elif(
            (self.state == self.WRITE_STATE) & (self.byte_num == 8) & (self.is_eol)
        ):
            m.d.comb += self.addr_o.eq(
                Cat(self.buffer[3], self.buffer[2], self.buffer[1], self.buffer[0])
            )
            m.d.comb += self.data_o.eq(
                Cat(self.buffer[7], self.buffer[6], self.buffer[5], self.buffer[4])
            )
            m.d.comb += self.valid_o.eq(1)
            m.d.comb += self.rw_o.eq(1)

        with m.Else():
            m.d.comb += self.addr_o.eq(0)
            m.d.comb += self.data_o.eq(0)
            m.d.comb += self.rw_o.eq(0)
            m.d.comb += self.valid_o.eq(0)

    def drive_fsm(self, m):
        with m.If(self.valid_i):
            with m.If(self.state == self.IDLE_STATE):
                m.d.sync += self.byte_num.eq(0)

                with m.If(self.data_i == ord("R")):
                    m.d.sync += self.state.eq(self.READ_STATE)

                with m.Elif(self.data_i == ord("W")):
                    m.d.sync += self.state.eq(self.WRITE_STATE)

            with m.If(self.state == self.READ_STATE):
                # buffer bytes if we don't have enough
                with m.If(self.byte_num < 4):
                    # if bytes aren't valid ASCII then return to IDLE state
                    with m.If(self.is_ascii_hex == 0):
                        m.d.sync += self.state.eq(self.IDLE_STATE)

                    # otherwise buffer them
                    with m.Else():
                        m.d.sync += self.buffer[self.byte_num].eq(self.from_ascii_hex)
                        m.d.sync += self.byte_num.eq(self.byte_num + 1)

                with m.Else():
                    m.d.sync += self.state.eq(self.IDLE_STATE)

            with m.If(self.state == self.WRITE_STATE):
                # buffer bytes if we don't have enough
                with m.If(self.byte_num < 8):
                    # if bytes aren't valid ASCII then return to IDLE state
                    with m.If(self.is_ascii_hex == 0):
                        m.d.sync += self.state.eq(self.IDLE_STATE)

                    # otherwise buffer them
                    with m.Else():
                        m.d.sync += self.buffer[self.byte_num].eq(self.from_ascii_hex)
                        m.d.sync += self.byte_num.eq(self.byte_num + 1)

                with m.Else():
                    m.d.sync += self.state.eq(self.IDLE_STATE)
        pass

    def elaborate(self, platform):
        m = Module()

        self.drive_ascii_signals(m)
        self.drive_output_bus(m)
        self.drive_fsm(m)

        return m


class UARTTransmitter(Elaboratable):
    def __init__(self, clocks_per_baud):
        self.clocks_per_baud = clocks_per_baud

        # Top-Level Ports
        self.data_i = Signal(8)
        self.start_i = Signal()
        self.done_o = Signal(reset=1)

        self.tx = Signal(reset=1)

        # Internal Signals
        self.baud_counter = Signal(range(clocks_per_baud))
        self.buffer = Signal(9)
        self.bit_index = Signal(4)

    def elaborate(self, platform):
        m = Module()

        with m.If((self.start_i) & (self.done_o)):
            m.d.sync += self.baud_counter.eq(self.clocks_per_baud - 1)
            m.d.sync += self.buffer.eq(Cat(self.data_i, 1))
            m.d.sync += self.bit_index.eq(0)
            m.d.sync += self.done_o.eq(0)
            m.d.sync += self.tx.eq(0)

        with m.Elif(~self.done_o):
            m.d.sync += self.baud_counter.eq(self.baud_counter - 1)
            m.d.sync += self.done_o.eq((self.baud_counter == 1) & (self.bit_index == 9))

            # A baud period has elapsed
            with m.If(self.baud_counter == 0):
                m.d.sync += self.baud_counter.eq(self.clocks_per_baud - 1)

                # Clock out another bit if there are any left
                with m.If(self.bit_index < 9):
                    m.d.sync += self.tx.eq(self.buffer.bit_select(self.bit_index, 1))
                    m.d.sync += self.bit_index.eq(self.bit_index + 1)

                # Byte has been sent, send out next one or go to idle
                with m.Else():
                    with m.If(self.start_i):
                        m.d.sync += self.buffer.eq(Cat(self.data_i, 1))
                        m.d.sync += self.bit_index.eq(0)
                        m.d.sync += self.tx.eq(0)

                    with m.Else():
                        m.d.sync += self.done_o.eq(1)
        return m


class TransmitBridge(Elaboratable):
    def __init__(self):
        # Top-Level Ports
        self.data_i = Signal(16)
        self.rw_i = Signal()
        self.valid_i = Signal()

        self.data_o = Signal(8, reset=0)
        self.start_o = Signal(1)
        self.done_i = Signal()

        # Internal Signals
        self.buffer = Signal(16, reset=0)
        self.count = Signal(4, reset=0)
        self.busy = Signal(1, reset=0)
        self.to_ascii_hex = Signal(8)
        self.n = Signal(4)

    def elaborate(self, platform):
        m = Module()

        m.d.comb += self.start_o.eq(self.busy)

        with m.If(~self.busy):
            with m.If((self.valid_i) & (~self.rw_i)):
                m.d.sync += self.busy.eq(1)
                m.d.sync += self.buffer.eq(self.data_i)

        with m.Else():
            # uart_tx is transmitting a byte:
            with m.If(self.done_i):
                m.d.sync += self.count.eq(self.count + 1)

                # Message has been transmitted
                with m.If(self.count > 5):
                    m.d.sync += self.count.eq(0)

                    # Go back to idle, or transmit next message
                    with m.If((self.valid_i) & (~self.rw_i)):
                        m.d.sync += self.buffer.eq(self.data_i)

                    with m.Else():
                        m.d.sync += self.busy.eq(0)

        # define to_ascii_hex
        with m.If(self.n < 10):
            m.d.comb += self.to_ascii_hex.eq(self.n + 0x30)
        with m.Else():
            m.d.comb += self.to_ascii_hex.eq(self.n + 0x41 - 10)

        # run the sequence
        with m.If(self.count == 0):
            m.d.comb += self.n.eq(0)
            m.d.comb += self.data_o.eq(ord("D"))

        with m.Elif(self.count == 1):
            m.d.comb += self.n.eq(self.buffer[12:16])
            m.d.comb += self.data_o.eq(self.to_ascii_hex)

        with m.Elif(self.count == 2):
            m.d.comb += self.n.eq(self.buffer[8:12])
            m.d.comb += self.data_o.eq(self.to_ascii_hex)

        with m.Elif(self.count == 3):
            m.d.comb += self.n.eq(self.buffer[4:8])
            m.d.comb += self.data_o.eq(self.to_ascii_hex)

        with m.Elif(self.count == 4):
            m.d.comb += self.n.eq(self.buffer[0:4])
            m.d.comb += self.data_o.eq(self.to_ascii_hex)

        with m.Elif(self.count == 5):
            m.d.comb += self.n.eq(0)
            m.d.comb += self.data_o.eq(ord("\r"))

        with m.Elif(self.count == 6):
            m.d.comb += self.n.eq(0)
            m.d.comb += self.data_o.eq(ord("\n"))

        with m.Else():
            m.d.comb += self.n.eq(0)
            m.d.comb += self.data_o.eq(0)

        return m
