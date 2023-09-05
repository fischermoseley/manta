from ..utils import *
from math import ceil

class InputProbe:
    def __init__(self, name, width, base_addr, strobe_addr, interface):
        assert isinstance(width, int), f"Probe {name} must have integer width."
        assert width > 0, f"Probe {name} must have positive width."

        self.name = name
        self.width = width
        self.strobe_addr = strobe_addr
        self.interface = interface

        n_addrs = ceil(self.width / 16)
        self.addrs = list(range(base_addr, base_addr + n_addrs))
        self.brackets = "" if self.width == 1 else f"[{self.width-1}:0] "

    def pulse_strobe_register(self):
        # pulse the strobe register
        self.interface.write(self.strobe_addr, 1)
        self.interface.write(self.strobe_addr, 0)
        strobe = self.interface.read(self.strobe_addr)
        if strobe != 0:
            raise ValueError("Unable to set strobe register to zero!")

    def get(self):
        self.pulse_strobe_register()
        return pack_16bit_words(self.interface.read(self.addrs))

class OutputProbe(InputProbe):
    def __init__(self, name, width, base_addr, strobe_addr, interface, initial_value):
        super().__init__(name, width, base_addr, strobe_addr, interface)
        self.initial_value = initial_value

    def set(self, value):
        # check that value is an integer
        assert isinstance(value, int), "Value must be an integer."

        # check that value is within range for the width of the probe
        if value > 0:
            assert value <= (2**self.width) - 1, f"Unsigned value too large for probe of width {self.width}"

        elif value < 0:
            assert abs(value) <= (2**(self.width-1))-1, f"Signed value too large for probe of width {self.width}"

        self.interface.write(self.addrs, unpack_16bit_words(value, len(self.addrs)))
        self.pulse_strobe_register()

class IOCore:
    def __init__(self, config, name, base_addr, interface):
        self.name = name
        self.base_addr = base_addr
        self.interface = interface

        # make sure we have ports defined
        assert ('inputs' in config) or ('outputs' in config), "No input or output ports specified."

        # check for unrecognized options
        for option in config:
            if option not in ["type", "inputs", "outputs", "user_clock"]:
                print(f"Warning: Ignoring unrecognized option '{option}' in IO core '{name}'")

        # add user clock
        self.user_clock = False
        if "user_clock" in config:
            assert isinstance(config["user_clock"], bool), "Option user_clock must be a boolean."
            self.user_clock = config["user_clock"]

        # add input probes to core
        self.input_probes = []
        last_used_addr = self.base_addr # start at one since strobe register is at BASE_ADDR
        if 'inputs' in config:
           for name, width in config["inputs"].items():
                probe = InputProbe(name, width, last_used_addr + 1, self.base_addr, interface)
                last_used_addr = probe.addrs[-1]
                self.input_probes.append(probe)

        # add output probes to core
        self.output_probes = []
        if 'outputs' in config:
            for name, params in config["outputs"].items():
                # get width and initial value from config
                if isinstance(params, int):
                    width = params
                    initial_value = 0

                elif "width" in params and "initial_value" in params:
                    width = params["width"]
                    initial_value = params["initial_value"]

                else:
                    raise ValueError(f"Unable to determine probe width and initial value for {name}")

                # add probe to core
                probe = OutputProbe(name, width, last_used_addr + 1, self.base_addr, interface, initial_value)
                last_used_addr = probe.addrs[-1]
                self.output_probes.append(probe)

        self.max_addr = last_used_addr

        # add friendly names to each probe
        # (so users can do io_core.probe.set() and get() for instance)
        for probe in self.input_probes + self.output_probes:
            setattr(self, probe.name, probe)

    def hdl_top_level_ports(self):
        ports = []

        if self.user_clock:
            ports.append(f"input wire {self.name}_user_clock")

        for probe in self.input_probes:
            ports.append(f"input wire {probe.brackets}{probe.name}")

        for probe in self.output_probes:
            ports.append(f"output reg {probe.brackets}{probe.name}")

        return ports

    def hdl_inst(self):
        inst = VerilogManipulator("io_core/io_core_inst_tmpl.v")
        inst.sub(self.name, "/* MODULE_NAME */")
        inst.sub(self.name + "_inst", "/* INST_NAME */")

        # tie user_clock to bus_clk if external clock is not being used
        if not self.user_clock:
            inst.sub("clk", "/* USER_CLK */")

        else:
            inst.sub(f"{self.name}_user_clk", "/* USER_CLK */")

        probes = {p.name:p.width for p in self.input_probes + self.output_probes}
        inst_ports = inst.net_conn(probes, trailing_comma=True)
        inst.sub(inst_ports, "/* INST_PORTS */")

        return inst.get_hdl()

    def hdl_def(self):
        io_core = VerilogManipulator("io_core/io_core_def_tmpl.v")
        io_core.sub(self.name, "/* MODULE_NAME */")
        io_core.sub(self.max_addr, "/* MAX_ADDR */")

        # generate declaration
        top_level_ports = ',\n'.join(self.hdl_top_level_ports())
        top_level_ports += ','
        io_core.sub(top_level_ports, "/* TOP_LEVEL_PORTS */")

        # generate memory handling
        io_core.sub(self.gen_read_case_statement_body(), "/* READ_CASE_STATEMENT_BODY */")
        io_core.sub(self.gen_write_case_statement_body(), "/* WRITE_CASE_STATEMENT_BODY */")

        # generate input and output probe buffers with initial values
        io_core.sub(self.gen_input_probe_bufs(), "/* INPUT_PROBE_BUFFERS */")
        io_core.sub(self.gen_output_probe_bufs(), "/* OUTPUT_PROBE_BUFFERS */")
        io_core.sub(self.gen_output_probe_initial_values(), "/* OUTPUT_PROBE_INITIAL_VALUES */")
        io_core.sub(self.gen_update_input_buffers(), "/* UPDATE_INPUT_BUFFERS */")
        io_core.sub(self.gen_update_output_buffers(), "/* UPDATE_OUTPUT_BUFFERS */")

        return io_core.get_hdl()

    def gen_read_case_statement_body(self):
        lines = []
        for probe in self.input_probes + self.output_probes:
            if probe.width <= 16:
                lines.append(f"BASE_ADDR + {probe.addrs[0]}: data_o <= {probe.name}_buf;")

            # assign 16-bit slices of each probe's buffer to each address taken by the probe
            else:
                for i in range(ceil(probe.width/16)):
                    top = ((i + 1) * 16) - 1
                    btm = i * 16
                    if top > probe.width - 1:
                        top = probe.width - 1
                    lines.append(f"BASE_ADDR + {probe.addrs[i]}: data_o <= {probe.name}_buf[{top}:{btm}];")

        return '\n'.join(lines)

    def gen_write_case_statement_body(self):
        lines = []
        for probe in self.output_probes:
            if probe.width <= 16:
                lines.append(f"BASE_ADDR + {probe.addrs[0]}: {probe.name}_buf <= data_i;")

            else:
                for i in range(ceil(probe.width/16)):
                    top = ((i + 1) * 16) - 1
                    btm = i * 16
                    if top > probe.width - 1:
                        top = probe.width - 1

                    lines.append(f"BASE_ADDR + {probe.addrs[i]}: {probe.name}_buf[{top}:{btm}] <= data_i;")

        return '\n'.join(lines)

    def gen_input_probe_bufs(self):
        lines = [f"reg {p.brackets}{p.name}_buf = 0;" for p in self.input_probes]
        return '\n'.join(lines)

    def gen_output_probe_bufs(self):
        lines = [f"reg {p.brackets}{p.name}_buf = {p.initial_value};" for p in self.output_probes]
        return '\n'.join(lines)

    def gen_output_probe_initial_values(self):
        lines = [f"{p.name} = {p.initial_value};" for p in self.output_probes]
        return '\n'.join(lines)

    def gen_update_input_buffers(self):
        lines = [f"{p.name}_buf <= {p.name};" for p in self.input_probes]
        return '\n'.join(lines)

    def gen_update_output_buffers(self):
        lines = [f"{p.name} <= {p.name}_buf;" for p in self.output_probes]
        return '\n'.join(lines)
