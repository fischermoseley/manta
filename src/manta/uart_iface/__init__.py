from ..utils import *

class UARTInterface:
    def __init__(self, config):
        # Warn if unrecognized options have been given
        for option in config:
            if option not in ["port", "clock_freq", "baudrate", "chunk_size", "verbose"]:
                print(f"Warning: Ignoring unrecognized option '{option}' in UART interface.")

        # Obtain port. Try to automatically detect port if "auto" is specified
        assert "port" in config, "No serial port provided to UART core."
        self.port = config["port"]

        # Check that clock frequency is provided and positive
        assert "clock_freq" in config, "Clock frequency not provided to UART core."
        assert config["clock_freq"] > 0, "Clock frequency must be positive."
        self.clock_freq = config["clock_freq"]

        # Check that baudrate is provided and positive
        assert "baudrate" in config, "Baudrate not provided to UART core."
        assert config["baudrate"] > 0, "Baudrate must be positive."
        self.baudrate = config["baudrate"]

        # Confirm core clock is sufficiently fast
        clocks_per_baud = self.clock_freq // self.baudrate
        assert clocks_per_baud >= 2
        self.clocks_per_baud = clocks_per_baud

        # Confirm we can match baudrate suffeciently well
        actual_baudrate = self.clock_freq / clocks_per_baud
        baudrate_error = 100 * abs(actual_baudrate - self.baudrate) / self.baudrate
        assert baudrate_error <= 5, \
            "Unable to match target baudrate - they differ by {baudrate_error}%"

        # Set chunk_size, which is the max amount of bytes that get dumped
        # to the OS driver at a time
        self.chunk_size = 256
        if "chunk_size" in config:
            self.chunk_size = config["chunk_size"]

        # Set verbosity
        self.verbose = False
        if "verbose" in config:
            self.verbose = config["verbose"]

    def open_port_if_not_alredy_open(self):
        if self.port == "auto":
            self.port = self.autodetect_port()

        if not hasattr(self, "ser"):
            import serial
            self.ser = serial.Serial(self.port, self.baudrate)

    def autodetect_port(self):
        # as far as I know the FT2232 is the only chip used on the icestick/digilent boards, so just look for that
        import serial.tools.list_ports

        recognized_devices = []
        for port in serial.tools.list_ports.comports():
            if (port.vid == 0x403) and (port.pid == 0x6010):
                recognized_devices.append(port)

        # board manufacturers seem to always make the 0th serial
        # interface on the FT2232 be for programming over JTAG,
        # and then the 1st to be for UART. as a result, we always
        # grab the device with the larger location

        rd = recognized_devices
        assert len(recognized_devices) == 2, f"Expected to see two serial ports for FT2232 device, but instead see {len(recognized_devices)}."
        assert rd[0].serial_number == rd[1].serial_number, "Serial numbers should be the same on both FT2232 ports - probably somehow grabbed ports on two different devices."
        return rd[0].device if rd[0].location > rd[1].location else rd[1].device

    def decode_response(self, response):
        """Make sure reponse from FPGA has the correct format, and return data contained within if so."""
        assert response is not None, "No reponse received."

        response_str = response.decode('ascii')
        assert response_str[0] == 'D', "Bad message recieved, incorrect preamble."
        assert response_str[-2] == '\r', "Bad message received, incorrect EOL."
        assert response_str[-1] == '\n', "Bad message received, incorrect EOL."
        assert len(response_str) == 7, f"Wrong number of bytes received, expecting 7 but got {len(response)}."

        return int(response_str[1:5], 16)


    def read(self, addr):
        # Perform type checks, output list of addresses
        if isinstance(addr, int):
            addrs = [addr]

        elif isinstance(addr, list):
            assert all(isinstance(a, int) for a in addr), \
                "Read addresses must be integer or list of integers."
            addrs = addr

        else:
            raise ValueError("Read addresses must be integer or list of integers.")

        # send data in chunks because the reponses will fill up the OS's
        # input buffer in no time flat
        self.open_port_if_not_alredy_open()

        inbound_bytes = b""
        for i in range(0, len(addrs), self.chunk_size):
            addr_chunk = addrs[i:i+self.chunk_size]

            outbound_bytes = [f"R{addr:04X}\r\n".encode('ascii') for addr in addr_chunk]
            outbound_bytes = b"".join(outbound_bytes)

            self.ser.write(outbound_bytes)

            inbound_bytes += self.ser.read(len(outbound_bytes))

        data = []
        for i in range(0, len(inbound_bytes), 7):
            response = inbound_bytes[i:i+7]
            data.append(self.decode_response(response))

        if isinstance(addr, int):
            return data[0]

        else:
            return data

    def write(self, addr, data):
        # Perform type checks, output list of addresses
        if isinstance(addr, int):
            assert isinstance(data, int), \
                "Data must also be integer if address is integer."
            addrs = [addr]
            datas = [data]

        elif isinstance(addr, list):
            assert all(isinstance(a, int) for a in addr), \
                "Write addresses must be integer or list of integers."

            assert all(isinstance(d, int) for d in data), \
                "Write data must be integer or list of integers."

            assert len(addr) == len(data), \
                "There must be equal number of write addresses and data."

            addrs = addr
            datas = data

        else:
            raise ValueError("Write addresses and data must be integer or list of integers.")

        # send data in chunks because the reponses will fill up the OS's
        # input buffer in no time flat
        self.open_port_if_not_alredy_open()

        for i in range(0, len(addrs), self.chunk_size):
            addr_chunk = addrs[i:i+self.chunk_size]
            data_chunk = datas[i:i+self.chunk_size]


            outbound_bytes = [f"W{a:04X}{d:04X}\r\n" for a, d in zip(addr_chunk, data_chunk)]
            outbound_bytes = [ob.encode('ascii') for ob in outbound_bytes]
            outbound_bytes = b"".join(outbound_bytes)

            self.ser.write(outbound_bytes)

    def hdl_top_level_ports(self):
        # this should return the probes that we want to connect to top-level, but like as a string of verilog
        return ["input wire rx", "output reg tx"]

    def rx_hdl_def(self):
        uart_rx_def = VerilogManipulator("uart_iface/uart_rx.v").get_hdl()
        bridge_rx_def = VerilogManipulator("uart_iface/bridge_rx.v").get_hdl()
        return uart_rx_def + '\n' + bridge_rx_def

    def tx_hdl_def(self):
        uart_tx_def = VerilogManipulator("uart_iface/uart_tx.v").get_hdl()
        bridge_tx_def = VerilogManipulator("uart_iface/bridge_tx.v").get_hdl()
        return bridge_tx_def + '\n' + uart_tx_def

    def rx_hdl_inst(self):
        rx = VerilogManipulator("uart_iface/uart_rx_bridge_rx_inst_tmpl.v")
        rx.sub(self.clocks_per_baud, "/* CLOCKS_PER_BAUD */")
        return rx.get_hdl()

    def tx_hdl_inst(self):
        tx = VerilogManipulator("uart_iface/uart_tx_bridge_tx_inst_tmpl.v")
        tx.sub(self.clocks_per_baud, "/* CLOCKS_PER_BAUD */")
        return tx.get_hdl()