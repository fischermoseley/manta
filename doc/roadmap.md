## Planned Work:

* _Clock Domain Crossing:_ You should be able to put cores in different clock domains - although I'm struggling to figure out where exactly this would be useful. Xilinx's ILA will let you have multiple cores and it doesn't care much which 
clock domain those are under, so some more investigation will be needed there. 

* _More Examples_, such as
    - SD card controller
    - BRAM controller
    - Pong, with controls via played through python on your machine. 

* _Configurable Trigger Location:_ Instead of always centering the downlink core's waveform around where the trigger condition is met, you might want to grab everything before or after the trigger. Or even things that are some number of clock cycles ahead or behind of the trigger. Being able to specify this 'holdoff' or 'position' in the downlink core configuration would be nice. Especially if it's something as simple as `beginning`, `middle`, `end`, or just a number of clock cycles.

* _Reconfigurable Trigger Modes_: Being able to switch between an incremental trigger and a single-shot trigger while the HDL's on the board might be useful. 

* _Incremental Triggering_: Only add things to the buffer when the trigger condition is met. Going to be super useful for audio applications.


## Potential Future Work:

The guiding principle behind adding features here is to just do a bunch of projects, run into annoying bugs, and see what'd be useful to have as a tool, and then implement that. That said, there's a few ideas I've been kicking around at the moment:

* _Configurable Clock Edge:_ Right now when we add a waveform to a VCD file, we assume that all the values change on the rising edge of the ILA clock. And that's true - we sample them on the rising edge of the input clock. I don't know if we'd want to add an option for clocking in things on the falling edge - I think that's going to make timing hard and students confused.

* _OpenCores Listing_: Might want to chuck this up on [https://opencores.org/projects](https://opencores.org/projects), just for kicks. 

* _FuseSoC integration_: This will probably exist in some headless-ish mode that separates manta's core generation and operation, but it'd be kinda nice for folks who package their projects with FuseSoC.

* _Test Manta on non-Xilinx FPGAs_: This is in progress for the Lattice iCE40 on the Icestick, and the Altera Cyclone IV on the DE0 Nano.

## Completed Features:

* _Packaging_: Manta should fundamentally be out of the way of the hardware developer, so it needs to live on the system, not as source code in the project repo. We learned this with `lab-bc` last semester - we couldn't update it easily and it ended up living in people's git repos. Which shouldn't be necessary since they're not responsible for versioning it - we are. Same mentality here.

* _Python API_: You should be able to run manta and scrape waveforms from the command line - but let's say you're working on a project that loads audio from an SD card, and you want to have a downlink core in incremental mode to pull your audio samples, but you want to export that as a .wav file. Or you want to do some filtering of the data with numpy. You should have a python API that lets you do that.