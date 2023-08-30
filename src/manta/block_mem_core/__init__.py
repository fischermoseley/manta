from ..utils import *

from math import ceil, log2

class BlockMemoryCore:
    def __init__(self, config, name, base_addr, interface):
        self.name = name
        self.base_addr = base_addr
        self.interface = interface

        # Warn if unrecognized options have been given
        for option in config:
            if option not in ["type", "depth", "width", "expose_port"]:
                print(f"Warning: Ignoring unrecognized option '{option}' in Block Memory core '{self.name}'")

        # Determine if we expose the BRAM's second port to the top of the module
        if "expose_port" in config:
            assert isinstance(config["expose_port"], bool), "Configuring BRAM exposure must be done with a boolean."
            self.expose_port = config["expose_port"]

        else:
            self.expose_port = True

        # Get depth
        assert "depth" in config, "Depth not specified for Block Memory core."
        assert config["depth"] > 0, "Block Memory core must have positive depth."
        assert isinstance(config["depth"], int), "Block Memory core must have integer depth."
        self.depth = config["depth"]

        # Get width
        assert "width" in config, "Width not specified for Block Memory core."
        assert config["width"] > 0, "Block Memory core must have positive width."
        assert isinstance(config["width"], int), "Block Memory core must have integer width."
        self.width = config["width"]

        self.addr_width = ceil(log2(self.depth))
        self.n_brams = ceil(self.width / 16)
        self.max_addr = self.base_addr + (self.depth * self.n_brams)

    def hdl_inst(self):
        inst = VerilogManipulator("block_mem_core/block_memory_inst_tmpl.v")
        inst.sub(self.name, "/* INST_NAME */")
        inst.sub(self.depth, "/* DEPTH */")
        inst.sub(self.width, "/* WIDTH */")
        return inst.get_hdl()

    def hdl_def(self):
        block_memory = VerilogManipulator("block_mem_core/block_memory.v").get_hdl()
        dual_port_bram = VerilogManipulator("block_mem_core/dual_port_bram.v").get_hdl()
        return block_memory + "\n" + dual_port_bram

    def hdl_top_level_ports(self):
        if not self.expose_port:
            return ""

        tlp = []
        tlp.append(f"input wire {self.name}_clk")
        tlp.append(f"input wire [{self.addr_width-1}:0] {self.name}_addr")
        tlp.append(f"input wire [{self.width-1}:0] {self.name}_din")
        tlp.append(f"output reg [{self.width-1}:0] {self.name}_dout")
        tlp.append(f"input wire {self.name}_we")
        return tlp

    def get_physical_addr(self, addr):
        if isinstance(addr, int):
            return addr + self.base_addr

        elif isinstance(addr, list):
            return [a + self.base_addr for a in addr]

        raise ValueError("Read address must be integer or list of integers.")

    def read(self, addr):
        return self.interface.read(self.get_physical_addr(addr))

    def write(self, addr, data):
        return self.interface.write(self.get_physical_addr(addr), data)