from amaranth.sim import Simulator
from manta.ethernet import UDPSourceBridge
from manta.utils import *


source_bridge = UDPSourceBridge()


def test_normie_ops():
    def testbench():
        yield source_bridge.data_i.eq(0)
        yield source_bridge.last_i.eq(0)
        yield source_bridge.valid_i.eq(0)
        yield
        yield

        yield source_bridge.data_i.eq(0x0000_0001)
        yield source_bridge.valid_i.eq(1)
        yield
        yield source_bridge.data_i.eq(0x1234_5678)
        yield
        yield source_bridge.valid_i.eq(0)
        yield
        yield

        yield source_bridge.valid_i.eq(1)
        yield source_bridge.data_i.eq(0x0000_0001)
        yield
        yield source_bridge.data_i.eq(0x90AB_CDEF)
        yield
        yield source_bridge.data_i.eq(0x0000_0000)
        yield
        yield source_bridge.data_i.eq(0x1234_5678)
        yield
        yield source_bridge.valid_i.eq(0)
        yield
        yield

    simulate(source_bridge, testbench, "source_bridge.vcd")
