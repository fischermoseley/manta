# ToDo

## IO Core
- add logic for ports >16 bits in width
- clock domain crossing

## Logic Analyzer Core
- need to finish up simulations, those might get broken out into separate testbenches for each module
- need to write tests - this will be hard because there's no template to go off of, so need to autogenerate before running tests
- clock domain crossing
- _Configurable Trigger Location:_ Instead of always centering the downlink core's waveform around where the trigger condition is met, you might want to grab everything before or after the trigger. Or even things that are some number of clock cycles ahead or behind of the trigger. Being able to specify this 'holdoff' or 'position' in the downlink core configuration would be nice. Especially if it's something as simple as `beginning`, `middle`, `end`, or just a number of clock cycles.
- _Reconfigurable Trigger Modes_: Being able to switch between an incremental trigger and a single-shot trigger while the HDL's on the board might be useful. 
- _Incremental Triggering_: Only add things to the buffer when the trigger condition is met. Going to be super useful for audio applications.
- _Configurable Clock Edge: (maybe)_ Right now when we add a waveform to a VCD file, we assume that all the values change on the rising edge of the ILA clock. And that's true: we sample them on the rising edge of the input clock. I don't know if we'd want to add an option for clocking in things on the falling edge - I think that's going to make timing hard and students confused.

## BRAM Core
- write HDL 
- write tests 
- write interface 

## Documentation
- Write out what bus transactions look like and how messages get passed. probably going to need wavedrom for this.

## Testing
- need to build out more tests for the python itself in test/api_gen
- try doing literally anything on Windows lol

## Meta
- need to write up some kind of tutorial for beta testers to run through
- probably want to make all the manta source pass verilator lint - doesn't look like this would be too hard to do
- maybe install local github actions runner to ubuntu/macos/linux VM with boards attached to it or something - just to make sure that examples actually work for real
- _OpenCores Listing_: Might want to chuck this up on [https://opencores.org/projects](https://opencores.org/projects), just for kicks. 
- _FuseSoC integration_: This will probably exist in some headless-ish mode that separates manta's core generation and operation, but it'd be kinda nice for folks who package their projects with FuseSoC.
- _Test Manta on non-Xilinx FPGAs_: This is in progress for the Lattice iCE40 on the Icestick, and the Altera Cyclone IV on the DE0 Nano.
