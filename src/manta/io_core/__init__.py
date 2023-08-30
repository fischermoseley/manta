from ..utils import *
from math import ceil

class Probe:
    def __init__(self, name, width, base_addr, interface):
        assert isinstance(width, int), f"Probe {name} must have integer width."
        assert width > 0, f"Probe {name} must have positive width."

        self.name = name
        self.width = width
        self.interface = interface

        n_addrs = ceil(self.width / 16)
        self.addrs = list(range(base_addr, base_addr + n_addrs))

class InputProbe(Probe):
    def __init__(self, name, width, base_addr, interface):
        super().__init__(name, width, base_addr, interface)

    def get(self):
        return pack_16bit_words(self.interface.read(self.addrs))

class OutputProbe(Probe):
    def __init__(self, name, width, base_addr, initial_value, interface):
        super().__init__(name, width, base_addr, interface)
        self.initial_value = initial_value

    def get(self):
        return pack_16bit_words(self.interface.read(self.addrs))

    def set(self, value):
        # check that value is an integer
        assert isinstance(value, int), "Value must be an integer."

        # check that value is within range for the width of the probe
        if value > 0:
            assert data <= (2**self.width) - 1, f"Unsigned value too large for probe of width {self.width}"

        elif value < 0:
            assert abs(data) <= (2**(self.width-1))-1, f"Signed value too large for probe of width {self.width}"

        data = unpack_16_bit_words(value)
        self.interface.write(self.addrs, data)

class IOCore:
    def __init__(self, config, name, base_addr, interface):
        self.name = name
        self.base_addr = base_addr

        # make sure we have ports defined
        assert ('inputs' in config) or ('outputs' in config), "No input or output ports specified."

        # check for unrecognized options
        for option in config:
            if option not in ["type", "inputs", "outputs", "user_clock"]:
                print(f"Warning: Ignoring unrecognized option '{option}' in IO core '{self.name}'")

        # add user clock
        self.user_clock = False
        if "user_clock" in config:
            assert isinstance(config["user_clock"], bool), "Option user_clock must be a boolean."
            self.user_clock = config["user_clock"]

        # add probes to core
        self.probes = []
        last_used_addr = self.base_addr # start at one since strobe register is at BASE_ADDR
        if 'inputs' in config:
           for name, width in config["inputs"].items():
                probe = InputProbe(name, width, last_used_addr + 1, interface)
                self.probes.append(probe)

                setattr(self, probe.name, probe) # add friendly name so users can do my_io_core.my_probe.set()
                last_used_addr = probe.addrs[-1]

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
                    raise ValueError(f"Unable to determine probe width and initial value for {probe}")

                # add probe to core
                probe = OutputProbe(name, width, last_used_addr + 1, initial_value, interface)
                self.probes.append(probe)

                setattr(self, probe.name, probe) # add friendly name so users can do my_io_core.my_probe.set()
                last_used_addr = self.probes[-1].addrs[-1]

        self.max_addr = last_used_addr

    def hdl_inst(self):
        inst = VerilogManipulator("io_core/io_core_inst_tmpl.v")
        inst.sub(self.name, "/* MODULE_NAME */")
        inst.sub(self.name + "_inst", "/* INST_NAME */")

        # tie user_clock to bus_clk if external clock is not being used
        if not self.user_clock:
            inst.sub("clk", "/* USER_CLK */")

        else:
            inst.sub(f"{self.name}_user_clk", "/* USER_CLK */")

        probes = {probe.name:probe.width for probe in self.probes}

        inst_ports = inst.net_conn(probes, trailing_comma=True)
        inst.sub(inst_ports, "/* INST_PORTS */")

        return inst.get_hdl()

    def gen_memory_handling(self):
        rcsb = "" # read case statement body
        wcsb = "" # write case statement body
        for probe in self.probes:
            if probe.width <= 16:
                rcsb += f"BASE_ADDR + {probe.addrs[0]}: data_o <= {probe.name}_buf;\n"

                if isinstance(probe, OutputProbe):
                    wcsb += f"BASE_ADDR + {probe.addrs[0]}: {probe.name}_buf <= data_i;\n"

            else:
                for i in range(ceil(probe.width/16)):
                    top = ((i + 1) * 16) - 1
                    btm = i * 16
                    if top > probe.width - 1:
                        top = probe.width - 1

                    rcsb += f"BASE_ADDR + {probe.addrs[i]}: data_o <= {probe.name}_buf[{top}:{btm}];\n"

                    if isinstance(probe, OutputProbe):
                        wcsb += f"BASE_ADDR + {probe.addrs[i]}: {probe.name}_buf[{top}:{btm}] <= data_i;\n"

        # remove trailing newline
        return rcsb.rstrip(), wcsb.rstrip()

    def gen_input_probe_bufs(self):
        ipb = []
        for probe in self.probes:
            if isinstance(probe, InputProbe):
                if probe.width == 1:
                    ipb.append(f"reg {probe.name}_buf = 0;")

                else:
                    ipb.append(f"reg [{probe.width-1}:0] {probe.name}_buf = 0;")

        return '\n'.join(ipb)



    def gen_output_probe_bufs(self):
        opb = []
        for probe in self.probes:
            if isinstance(probe, OutputProbe):
                if probe.width == 1:
                    opb.append(f"reg {probe.name}_buf = {probe.initial_value};")

                else:
                    opb.append(f"reg [{probe.width-1}:0] {probe.name}_buf = {probe.initial_value};")

        return '\n'.join(opb)


    def gen_output_probe_initial_values(self):
        opiv = []
        for probe in self.probes:
            if isinstance(probe, OutputProbe):
                opiv.append(f"{probe.name} = {probe.initial_value};")

        return '\n'.join(opiv)


    def gen_update_input_buffers(self):
        uib = []
        for probe in self.probes:
            if isinstance(probe, InputProbe):
                uib.append(f"{probe.name}_buf <= {probe.name};")

        return '\n'.join(uib)

    def gen_update_output_buffers(self):
        uob = []
        for probe in self.probes:
            if isinstance(probe, OutputProbe):
                uob.append(f"{probe.name} <= {probe.name}_buf;")

        return '\n'.join(uob)

    def hdl_def(self):
        io_core = VerilogManipulator("io_core/io_core_def_tmpl.v")
        io_core.sub(self.name, "/* MODULE_NAME */")
        io_core.sub(self.max_addr, "/* MAX_ADDR */")

        # generate declaration
        top_level_ports = ',\n'.join(self.hdl_top_level_ports())
        top_level_ports += ','
        io_core.sub(top_level_ports, "/* TOP_LEVEL_PORTS */")

        # generate memory handling
        rcsb, wcsb = self.gen_memory_handling()
        io_core.sub(rcsb, "/* READ_CASE_STATEMENT_BODY */")
        io_core.sub(wcsb, "/* WRITE_CASE_STATEMENT_BODY */")

        # generate input and output probe buffers
        io_core.sub(self.gen_input_probe_bufs(), "/* INPUT_PROBE_BUFFERS */")
        io_core.sub(self.gen_output_probe_bufs(), "/* OUTPUT_PROBE_BUFFERS */")
        io_core.sub(self.gen_output_probe_initial_values(), "/* OUTPUT_PROBE_INITIAL_VALUES */")
        io_core.sub(self.gen_update_input_buffers(), "/* UPDATE_INPUT_BUFFERS */")
        io_core.sub(self.gen_update_output_buffers(), "/* UPDATE_OUTPUT_BUFFERS */")

        return io_core.get_hdl()

    def hdl_top_level_ports(self):
        ports = []

        if self.user_clock:
            ports.append(f"input wire {self.name}_user_clock")

        for probe in self.probes:
            net_type = "input wire " if isinstance(probe, InputProbe) else "output reg "
            name_def = probe.name if probe.width == 1 else f"[{probe.width-1}:0] {probe.name}"
            ports.append(net_type + name_def)

        return ports