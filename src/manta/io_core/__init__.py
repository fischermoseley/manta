from ..hdl_utils import *

class IOCoreProbe:
    def __init__(self, name, width, direction, base_addr, interface):
        self.name = name
        self.width = width
        self.direction = direction
        self.base_addr = base_addr
        self.interface = interface

    def set(self, data):
        # make sure that we're an output probe
        assert self.direction == "output", "Cannot set value of input port."

        # check that value is within range for the width of the probe
        assert isinstance(data, int), "Data must be an integer."
        if data > 0:
            assert data <= (2**self.width) - 1, f"Unsigned value too large for probe of width {self.width}"

        elif data < 0:
            assert data >= -(2**(self.width-1))-1, f"Signed value too large for probe of width {self.width}"
            assert data <= (2**(self.width-1))-1, f"Signed value too large for probe of width {self.width}"

        self.interface.write(self.base_addr, data)

    def get(self):
        return self.interface.read(self.base_addr)

class IOCore:
    def __init__(self, config, name, base_addr, interface):
        self.name = name
        self.base_addr = base_addr
        self.interface = interface

        # Warn if unrecognized options have been given
        for option in config:
            if option not in ["type", "inputs", "outputs"]:
                print(f"Warning: Ignoring unrecognized option '{option}' in IO core '{self.name}'")

        # make sure we have ports defined
        assert ('inputs' in config) or ('outputs' in config), "No input or output ports specified."

        # add input probes to core
        self.probes = []
        probe_base_addr = self.base_addr
        if 'inputs' in config:
           for name, width in config["inputs"].items():
                # make sure inputs are of reasonable width
                assert isinstance(width, int), f"Probe {name} must have integer width."
                assert width > 0, f"Probe {name} must have positive width."

                probe = IOCoreProbe(name, width, "input", probe_base_addr, self.interface)

                # add friendly name, so users can do Manta.my_io_core.my_probe.set() for example
                setattr(self, name, probe)
                self.probes.append(probe)

                self.max_addr = probe_base_addr
                probe_base_addr += 1

        # add output probes to core
        if 'outputs' in config:
            for name, width in config["outputs"].items():
                # make sure inputs are of reasonable width
                assert isinstance(width, int), f"Probe {name} must have integer width."
                assert width > 0, f"Probe {name} must have positive width."

                probe = IOCoreProbe(name, width, "output", probe_base_addr, self.interface)

                # add friendly name, so users can do Manta.my_io_core.my_probe.set() for example
                setattr(self, name, probe)
                self.probes.append(probe)

                self.max_addr = probe_base_addr
                probe_base_addr += 1


    def hdl_inst(self):
        inst = VerilogManipulator("io_core/io_core_inst_tmpl.v")
        inst.sub(self.name, "/* MODULE_NAME */")
        inst.sub(self.name + "_inst", "/* INST_NAME */")

        probes = {probe.name:probe.width for probe in self.probes}

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
        rcsb = "" # read case statement body
        wcsb = "" # write case statement body
        for probe in self.probes:

            # add to read block
            if probe.width == 16:
                rcsb += f"{probe.base_addr}: data_o <= {probe.name};\n"

            else:
                rcsb += f"{probe.base_addr}: data_o <= {{{16-probe.width}'b0, {probe.name}}};\n"


            # if output, add to write block
            if probe.direction == "output":
                if probe.width == 1:
                    wcsb += f"{probe.base_addr}: {probe.name} <= data_i[0];\n"

                elif probe.width == 16:
                    wcsb += f"{probe.base_addr}: {probe.name} <= data_i;\n"

                else:
                    wcsb += f"{probe.base_addr}: {probe.name} <= data_i[{probe.width-1}:0];\n"

        # remove trailing newline
        rcsb = rcsb.rstrip()
        wcsb = wcsb.rstrip()

        io_core.sub(rcsb, "/* READ_CASE_STATEMENT_BODY */")
        io_core.sub(wcsb, "/* WRITE_CASE_STATEMENT_BODY */")

        return io_core.get_hdl()



    def hdl_top_level_ports(self):
        ports = []
        for probe in self.probes:
            net_type = "input wire " if probe.direction == "input" else "output reg "
            name_def = probe.name if probe.width == 1 else f"[{probe.width-1}:0] {probe.name}"
            ports.append(net_type + name_def)

        return ports