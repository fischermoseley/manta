from ..hdl_utils import *

class LUTMemoryCore:
    def __init__(self, config, name, base_addr, interface):
        self.name = name
        self.base_addr = base_addr
        self.interface = interface

        # Warn if unrecognized options have been given
        for option in config:
            if option not in ["type", "size"]:
                print(f"Warning: Ignoring unrecognized option '{option}' in LUT Memory '{self.name}'")

        assert "size" in config, "Size not specified for LUT RAM core."
        assert config["size"] > 0, "LUT RAM must have positive size."
        assert isinstance(config["size"], int), "LUT RAM must have integer size."
        self.size = config["size"]

        self.max_addr = self.base_addr + self.size - 1

    def hdl_inst(self):
        inst = VerilogManipulator("lut_mem_core/lut_mem_inst_tmpl.v")
        inst.sub(self.size, "/* DEPTH */")
        inst.sub(self.name, "/* INST_NAME */")
        return inst.get_hdl()

    def hdl_def(self):
        return VerilogManipulator("lut_mem_core/lut_mem.v").get_hdl()

    def hdl_top_level_ports(self):
        # no top_level connections since this core just lives on the bus
        return ""

    def read(self, addr):
        return self.interface.read_register(addr + self.base_addr)

    def write(self, addr, data):
        return self.interface.write_register(addr + self.base_addr, data)