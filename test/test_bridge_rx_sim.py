from amaranth.sim import Simulator
from manta.uart import RecieveBridge
from manta.utils import *


bridge_rx = RecieveBridge()


def verify_read_decoding(bytes, addr):
    """
    Send a series of bytes to the receive bridge, and verify that the bridge places
    a read request with the appropriate address on the internal bus.
    """
    valid_asserted = False
    yield bridge_rx.valid_i.eq(1)

    for i, byte in enumerate(bytes):
        yield bridge_rx.data_i.eq(byte)

        if (yield bridge_rx.bus_o.valid) and (i > 0):
            valid_asserted = True
            if (yield bridge_rx.bus_o.addr) != addr:
                raise ValueError("wrong addr!")

            if (yield bridge_rx.bus_o.rw) != 0:
                raise ValueError("wrong rw!")

            if (yield bridge_rx.bus_o.data) != 0:
                raise ValueError("wrong data!")

        yield

    yield bridge_rx.valid_i.eq(0)
    yield bridge_rx.data_i.eq(0)

    if not valid_asserted and not (yield bridge_rx.bus_o.valid):
        raise ValueError("Bridge failed to output valid message.")


def verify_write_decoding(bytes, addr, data):
    """
    Send a series of bytes to the receive bridge, and verify that the bridge places
    a write request with the appropriate address and data on the internal bus.
    """
    valid_asserted = False
    yield bridge_rx.valid_i.eq(1)

    for i, byte in enumerate(bytes):
        yield bridge_rx.data_i.eq(byte)

        if (yield bridge_rx.bus_o.valid) and (i > 0):
            valid_asserted = True
            if (yield bridge_rx.bus_o.addr) != addr:
                raise ValueError("wrong addr!")

            if (yield bridge_rx.bus_o.rw) != 1:
                raise ValueError("wrong rw!")

            if (yield bridge_rx.bus_o.data) != data:
                raise ValueError("wrong data!")

        yield

    yield bridge_rx.valid_i.eq(0)
    yield bridge_rx.data_i.eq(0)

    if not valid_asserted and not (yield bridge_rx.bus_o.valid):
        raise ValueError("Bridge failed to output valid message.")


def verify_bad_bytes(bytes):
    """
    Send a series of bytes to the receive bridge, and verify that the bridge does not
    place any transaction on the internal bus.
    """
    yield bridge_rx.valid_i.eq(1)

    for byte in bytes:
        yield bridge_rx.data_i.eq(byte)

        if (yield bridge_rx.bus_o.valid):
            raise ValueError("Bridge decoded invalid message.")

        yield

    yield bridge_rx.valid_i.eq(0)


def test_read_decode():
    def testbench():
        yield from verify_read_decoding(b"R0000\r\n", 0x0000)
        yield from verify_read_decoding(b"R1234\r\n", 0x1234)
        yield from verify_read_decoding(b"RBABE\r\n", 0xBABE)
        yield from verify_read_decoding(b"R5678\n", 0x5678)
        yield from verify_read_decoding(b"R9ABC\r", 0x9ABC)

    simulate(bridge_rx, testbench)


def test_write_decode():
    def testbench():
        yield from verify_write_decoding(b"W12345678\r\n", 0x1234, 0x5678)
        yield from verify_write_decoding(b"WDEADBEEF\r\n", 0xDEAD, 0xBEEF)
        yield from verify_write_decoding(b"WDEADBEEF\r", 0xDEAD, 0xBEEF)
        yield from verify_write_decoding(b"WB0BACAFE\n", 0xB0BA, 0xCAFE)

    simulate(bridge_rx, testbench)


def test_no_decode():
    def testbench():
        yield from verify_bad_bytes(b"RABC\r\n")
        yield from verify_bad_bytes(b"R12345\r\n")
        yield from verify_bad_bytes(b"M\r\n")
        yield from verify_bad_bytes(b"W123456789101112131415161718191201222\r\n")
        yield from verify_bad_bytes(b"RABCG\r\n")
        yield from verify_bad_bytes(b"WABC[]()##*@\r\n")
        yield from verify_bad_bytes(b"R\r\n")

    simulate(bridge_rx, testbench)
