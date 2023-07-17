from manta import Manta
from time import sleep

m = Manta('manta.yaml')

i = 0
direction = "left"

while True:
    if direction == "left":
        if i == 15:
            direction = "right"
            i = i - 1
            m.my_io_core.led16_r.set(1)
            m.my_io_core.led16_g.set(0)
            m.my_io_core.led16_b.set(1)
        else:
            i = i + 1
    
    if direction == "right":
        if i == 0:
            direction = "left"
            i = i + 1
            m.my_io_core.led16_r.set(0)
            m.my_io_core.led16_g.set(1)
            m.my_io_core.led16_b.set(0)
        
        else:
            i = i - 1
    
    m.my_io_core.led.set(2**i)
    print(f"Input Ports:")
    print(f"  btnu: {m.my_io_core.btnu.get()}")
    print(f"  btnd: {m.my_io_core.btnd.get()}")
    print(f"  btnr: {m.my_io_core.btnr.get()}")
    print(f"  btnl: {m.my_io_core.btnl.get()}")
    print(f"  btnc: {m.my_io_core.btnc.get()}")
    print(f"  sw: {m.my_io_core.sw.get()}\n")
    sleep(0.5)

