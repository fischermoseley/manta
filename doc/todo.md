## IO Core
- add interface read/write to python
- test examples that build
- update IO core read/write memory handling to be less ugly
- add logic for ports >16 bits in width
- figure out what happens for module naming - it's possible we could have two modules that have the same ports but have different names
    - do we say that port names have to be globally unique? or do we allow something like `module_name_module_type_inst` for example

## Logic Analyzer Core
- need to finish up simulations, those might get broken out into separate testbenches for each module
- need to write tests - this will be hard because there's no template to go off of, so need to autogenerate before running tests

## BRAM Core
- write HDL 
- write tests 
- write interface 

## Python API
- find a better way of handling tabs
- make finding a serial port possible even if no cores are configured
- make autodetecting and automatically selecting a serial device possible
    - if we see a FT2232 on the device we should grab it

## Documentation
- Move stuff out of readme.md and into the docs front page - right now information is duplicated
- Write out what technologies are being used here (iverilog for sim, gtkwave for vcd, makefile for simulation/lint/pushing to pypi, github actions for automated test and building the doc site, python for autogeneration, verilator for lint. for docs, mkdoc-material for the site, wavedrom for timing diagrams and draw.io for block diagrams)
- Write out where stuff is being stored - `test/` contains all the systemverilog testbenches, `src/manta` contains all verilog and python needed to generate and run the cores, `doc/` contains the documentation site source files, `.github/` contains the github actions config, `examples/` is exactly what it sounds like

- Write out the anatomy of manta.v and how `Manta` generates that
- Write out what methods need to be implemented for Manta.generate_hdl() to actually be able to pick up on the cores
- Write out what bus transactions look like and how messages get passed. probably going to need wavedrom for this.

## Testing
- need to add tests for the python itself - does it recognize bad yaml files and produce the right errors when trying to build from them? are good manta files synthesizeable?
- try doing literally anything on Windows lol

## Meta
- probably want to make all the manta source pass verilator lint - doesn't look like this would be too hard to do
- maybe install local github actions runner to ubuntu/macos/linux VM with boards attached to it or something - just to make sure that examples actually work for real