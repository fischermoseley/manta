# ToDo

# Deadlines
- _04/12_ - BRAM Core
- _04/13_ - Logic Analyzer working with >16 bit inputs. Currently held up by the sample memory, but will be resolved once BRAM core is ruggedized.
- _04/14_ - CDC in the Logic Analyzer. Should be handled automatically, but just need to test it - probably with a SD card example.
- _04/15_ - _fischer's day off_
- _04/16_ - VCD export and .mem export for hardware-in-the-loop

__release to PyPI lists - manta v0.0.1 out__

- _04/17_ - write logic analyzer lab
- _04/18_ - beta tester round 2, run logic analyzer lab. ethernet tx if there's time
- _04/19_ - Ethernet TX
- _04/20_ - Ethernet TX
- _04/21_ - Ethernet TX
- _04/22_ - _fischer's day off_
- _04/23_ - _fischer's day off_

- _04/28/23_ - start writing docs site, move appropriate bits into thesis
- _05/05/23_ - slack week
- _05/12/23_ - thesis due
- _05/19/23_ - thesis actually due


## IO Core
- clock domain crossing
- add logic for ports >16 bits in width

## Logic Analyzer Core
- clock domain crossing
- trigger modes
- external trigger


## Meta
- consider making manta pass verilator lint - or at least as much of it as possible
- [opencores](https://opencores.org/projects) listing
- [fusesoc](https://github.com/fusesoc/fusesoc.github.io)
- port more examples to the icestorm FPGA
- hardware-in-the-loop testing?