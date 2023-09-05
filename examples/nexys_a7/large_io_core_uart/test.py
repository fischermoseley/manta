from manta import Manta
from random import randint
m = Manta('manta.yaml')

n_tests = 100
for i in range(n_tests):
    print(f"-> Beginning test {i} of {n_tests}")
    probe4 = randint(0, 1)
    m.io_core.probe4.set(probe4)
    assert m.io_core.probe4.get() == probe4
    assert m.io_core.probe0.get() == probe4

    probe5 = randint(0, 3)
    m.io_core.probe5.set(probe5)
    assert m.io_core.probe5.get() == probe5
    assert m.io_core.probe1.get() == probe5

    probe6 = randint(0, 255)
    m.io_core.probe6.set(probe6)
    assert m.io_core.probe6.get() == probe6
    assert m.io_core.probe2.get() == probe6

    probe7 = randint(0, (2**20)-1)
    m.io_core.probe7.set(probe7)
    assert m.io_core.probe7.get() == probe7
    assert m.io_core.probe3.get() == probe7
