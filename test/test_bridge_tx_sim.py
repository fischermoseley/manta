from amaranth.sim import Simulator
from manta.uart import TransmitBridge
from manta.utils import *
from random import randint, sample


bridge_tx = TransmitBridge()


def verify_encoding(data, bytes):
    """
    Place a read response on the internal bus, and verify that the sequence of bytes
    sent from TransmitBridge matches the provided bytestring `bytes`.

    This function also models an ideal UARTTransmitter module, which begins transmitting
    bytes when `start` is asserted, and reports when it is done by asserting `done`.
    """

    # Place a read response on the internal bus
    yield bridge_tx.data_i.eq(data)
    yield bridge_tx.valid_i.eq(1)
    yield bridge_tx.rw_i.eq(0)
    yield bridge_tx.done_i.eq(1)

    yield

    yield bridge_tx.data_i.eq(0)
    yield bridge_tx.valid_i.eq(0)
    yield bridge_tx.rw_i.eq(0)

    yield

    # Model the UARTTransmitter
    sent_bytes = b""
    iters = 0

    while len(sent_bytes) < len(bytes):
        # If start_o is asserted, set done_i to zero, then delay, then set it back to one
        if (yield bridge_tx.start_o):
            yield bridge_tx.done_i.eq(0)
            sent_bytes += (yield bridge_tx.data_o).to_bytes(1, "big")

            yield bridge_tx.done_i.eq(0)
            for _ in range(10):
                yield

            yield bridge_tx.done_i.eq(1)
            yield

        # Time out if not enough bytes after trying to get bytes 15 times
        iters += 1
        if iters > 15:
            raise ValueError("Timed out waiting for bytes.")

    # Verify bytes sent from ReceiveBridge match expected_bytes
    if sent_bytes != bytes:
        raise ValueError(f"Received {sent_bytes} instead of {bytes}.")


def test_some_random_values():
    def testbench():
        for i in sample(range(0xFFFF), k=5000):
            expected = f"D{i:04X}\r\n".encode("ascii")
            print(i)
            yield from verify_encoding(i, expected)

    simulate(bridge_tx, testbench)
