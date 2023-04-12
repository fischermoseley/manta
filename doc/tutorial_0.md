# Background

We've got a couple things we're hoping to get out of today:
- Say hi! Been a little while since we've seen ya'll, wanna see how you're dooooinnnnnnn
- Get your initial reactions to some tools we've cooked up. We've spent a _lot_ of time trying to nail the ergonomics of these and we want to see how comfortable it is to use them.
- See if they work. Because if there's any major bugs you're probably going to run into them __real__ quick.
- See where they lead your imagination to - these tools were designed to improve 6.205's trademark _I'm Sitting At A Terminal For Twenty Hours_ experience, but we have some ideas about these could fit in designing programmable hardware in a more general sense.

We'll be asking you a bunch of questions as you work through things, and we'd love to hear your thoughts as they come up. Fundamentally, ya'll are the people we're trying to help with these projects, so if something sucks, tell us. And if something's great, tell us that too :)

We've designed today's playtest to take about an hour, with the first half devoted to new tools for generating Verilog, and the last half devoted to new tools for building it. We'll be running some battle-tested 6.205 content through these tools, so this should hopefully feel nice and familiar - or at least familiar.


## Install Manta

Go ahead and install Manta with:

`pip install git+https://github.com/fischermoseley/manta.git`

You're also welcome to install Manta in a virtual environment using `venv` or `conda`, if that's your jam. Manta has very loose dependency requirements (just needs pySerial, yaml, and pyVCD), so it ~~won't~~ shouldn't break your system Python if you choose not to use a virtual environment. That's how I have it set up on all my machine and ~~it~~ that part of it hasn't broken yet.

If that doesn't work, just run the install script that's in this repo:

`git clone git@github.com:fischermoseley/lab_x_template.git`

And when you need to update your installation when I inevitably have to push a hotfix in the next half hour, you can do so with:

`pip install --upgrade --force-reinstall mantaray`

And today's template code is in the following repo, if you haven't cloned it already:

`git clone git@github.com:fischermoseley/lab_x_template.git`

## What Exactly is This Going To Do lmao

Glad you asked. Manta's what I've been working on for the last little bit, and it's basically a set of tools that helps you get data onto (and off of) the FPGA in a handful of ways. The immediate goal is to help with debugging designs on your FPGA, but it's also useful for getting data into and out of your design in a more general sense. What do I mean? Let's say you're:

- Making an accelerator for matrix multiplication, but you want to focus on the accelerator and don't want to bother writing an ethernet interface to get data into/out of it.
- Making a musical instrument out of stepper motors, and you want to tweak your audio filters, but don't want to rebuild your Verilog every time you do so.
- Making a UDP layer, and you want to see what your ARP table looks like when you plug your FPGA into MITnet.
- Making a music player, and you want to interface with a SD card controller that You Didn't Write And Nobody Understands, and you'd like to know why your requests to read from the card don't return any data.
- Making a L2 Ethernet layer, and your Verilog passes all of our testbenches, but doesn't work when the staff comes to check it off, and has no errors in the build logs.
- ...

Everything above could benefit from being able to peer into your FPGA fabric and inspect/modify values in real time. If you were lucky enough last semester, we brought out the _Integrated Logic Analyzer_ (or ILA) to do this, but that required firing up Vivado's GUI, and listening to a bunch of loathsome comments from the TAs. Manta superceeds the ILA, but it also has some other operating modes that we'll poke with later. But for now, this is the intent.

Manta's a glorified python script that takes a configuration file that describes a bunch of __cores__, and then spices and dices a bunch of Verilog source files together to produce a module that contains the cores you asked for. This module also grabs onto the UART interface on your FPGA, letting your computer interact with these cores over UART. Manta provides a nice Python API for this too, so you can write your own scripts. We'll try our hand at some of this today 🤠

### Configuring Manta

For today's test, we'll be configuring a __IO Core__, which is exactly what it sounds like. It's a core with a set of inputs and outputs that you can write to or get the values of. For simplicity (and because we expect everything else to break lol), we'll be connecting it to the switches and LEDs on your board, and then asking you to write some kind of python that manipulates the LEDs in response to the switches. Simple enough.

Manta gets configured with a YAML file, which looks about like this:

```yaml
---
cores:
  my_io_core:
    type: io

    inputs:
      spike: 1
      jet: 12
      valentine: 6
      ed: 9
      ein: 16

    outputs:
      shepherd: 10
      wrex: 1
      tali: 5
      garrus: 3

uart:
  port: "auto"
  baudrate: 115200
  clock_freq: 100000000
```

This defines an IO Core, and then adds a few signals to it, specifying their widths along the way. Go ahead and make a `manta.yaml` file that controls `led[15:0]`, along with the RGB leds on 16 and 17. And also add the switches to your IO core too.

Manta itself actually doesn't care what you name your nets (it's not going to try to automatically connect them to the pins or anything) but naming them with the signal they're supposed to connect to makes things a bit easier for us.

Once you've got all the signals added to your IO core, we'll want to generate the Verilog that implements the core. Go ahead and run:

`manta gen <path_to_config_file> <path_to_output_verilog>`

which in our case is:

`manta gen manta.yaml src/manta.v`

And if you're confused about how this command works, just run `manta help`.

Go ahead and have a look at the Verilog file it just spat out - it contains a definition for a module called `manta`, which we'll instantiate in our `top_level` module. There might be something in the autogenerated Verilog that might be useful for this ;)

Once you've got the ports on the `manta` module wired up to the ports on your board, go ahead and build it. If you've still got it, pay an old friend a visit and build your Verilog with lab-bc. There's a copy of it here if you need it. We've got tissues available if you get a little teary-eyed seeing it faithfully munching through your code again - we know we did.

If you don't have lab-bc available, you can just build with your local copy of Vivado, because you're sitting in front of lab computer:

`vivado -mode batch -source build.tcl`

Flash the bitstream once it's done building. Lemme know if you get any weird errors in the build logs.

### Using the Python API

Excellent, you've put Manta on your FPGA! Let's try talking to it from our computers - go ahead and run the following python file:

```python
from manta import Manta
m = Manta('manta.yaml')
m.my_io_core.led.set(1)

print(my_io_core.btnc.get())
```

This should change the value of the LED, and print out the logical value of the button on your board. If this works - congratulations! Go ahead and see if you can write a python script that does something interesting with your IO core - maybe it makes the LED bounce back and forth, maybe it counts up and down when you push `btnu` and `btnd`, maybe it submits RFPs for your CPW events. I'll let you guess the syntax on how to work with the API - lemme know if you run into troubles, and show me what you have once it's working.


### Fischer's Filosophical Feelings

This most likely wasn't super awe-inspiring - after all we just twiddled some registers on the chip. But hopefully the utility of something like this is apparent. We'll check out other cores manta has to offer in the future, but it also has:

- A _Logic Analyzer_ core, which does pretty much exactly the same thing as the ILA - it dumps whatever signals you'd like into a .vcd file, which you can poke around with in GTKWave. But it also exports those to a .mem file, which you can use to load those same signals into your iVerilog simulations. This lets you run your code through the same signals that it'll see once it's on the FPGA, and debug it in simulation instead of hardware. Imagine doing this for your PS/2 keyboards in lab02 - things passed the online checker and seemed to work in simulation, but didn't work with the actual keyboard.

- A _Block Memory_ core, which lets you set the contents of a BRAM from your machine. Want to change the contents of your image sprites in near real-time? Want to do your lab04 image processing from your laptop's webcam instead of a potato-quality camera?

- An _Ethernet Interface_ if you need to do any of the above, but _super speedy_. Today we just ran things over UART, but that's slow as mollasses and sometimes you just [gotta go fast](https://www.youtube.com/watch?v=LIfgMI8qLBk).

### SWAG DISTRIBUTION

Congrats on being an alpha tester!! I've got stickers and we've got pizza for ya to say thank you :)