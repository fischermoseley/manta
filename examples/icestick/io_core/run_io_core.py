from manta import Manta
from time import sleep

m = Manta('manta.yaml')

i = 0
while True:
    i = (i+1) % 5

    if(i==0):
        m.my_io_core.LED0.set(1)
        m.my_io_core.LED1.set(0)
        m.my_io_core.LED2.set(0)
        m.my_io_core.LED3.set(0)
        m.my_io_core.LED4.set(0)
    
    if(i==1):
        m.my_io_core.LED0.set(0)
        m.my_io_core.LED1.set(1)
        m.my_io_core.LED2.set(0)
        m.my_io_core.LED3.set(0)
        m.my_io_core.LED4.set(0)
    
    if(i==2):
        m.my_io_core.LED0.set(0)
        m.my_io_core.LED1.set(0)
        m.my_io_core.LED2.set(1)
        m.my_io_core.LED3.set(0)
        m.my_io_core.LED4.set(0)
        
    if(i==3):
        m.my_io_core.LED0.set(0)
        m.my_io_core.LED1.set(0)
        m.my_io_core.LED2.set(0)
        m.my_io_core.LED3.set(1)
        m.my_io_core.LED4.set(0)
    
    if(i==4):
        m.my_io_core.LED0.set(0)
        m.my_io_core.LED1.set(0)
        m.my_io_core.LED2.set(0)
        m.my_io_core.LED3.set(0)
        m.my_io_core.LED4.set(1)

    sleep(0.1)