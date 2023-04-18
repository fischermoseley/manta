## Welcome back!
Howdy and welcome back to the party! Today's format is going to be a little different - we'll be splitting ya'll up into two groups and having one set test Manta, and one set test lab-bc 2.0 - in _parallel_. This will hopefully take less time, give us some more meaningful tests, and just be better on the whole. It'd be kinda embarassing if this doesn't work, parallelization is kind of our _whole thing_.

## Update Manta
There's been a fair bit of work since this time last week! Actually I'm curious how many commits there've been...

```
$ git log --since='1 week ago' | grep Fischer | wc -l

41
```

Oh god - we should definitely update Manta. And I should definitely, like, go outside or something. Go ahead and use the instructions on the [installation](../installation) page to get yourself up to date.

## Boilerplate
While you've got a terminal open, go ahead and grab the starter code from fischer's [super exclusive, boutique, and bouguie code hosting site](https://github.com/fischermoseley/tutorial_2_template)

## The fun part!
Today we'll be experimenting with the most powerful Manta feature - the Logic Analyzer core. If we ever connected an ILA to your code last semester (or used a proper, benchtop logic analyzer like the ones on top the tables), then this will feel pretty familiar. But if not, perfect :)

The logic analyzer core connects to a set of singals that you want to investigate, which you do by _capturing_ them. When a _trigger condition_ is met, the logic analyzer core will record the value of each signal to internal memory, until that memory is full. That memory is then read back by the host machine, and exported to a `.vcd` file which we can open in GTKWave and poke around with.

And later, we'll "play back" that capture data in our own simulation, where we'll prototype a PS2 decoder. And if it works there on data captured from the real world, it should work just dandy when we go to implement it in hardware.

We'll be kicking the tires on the Logic Analyzer core in the context of the PS/2 keyboards we used in [lab02](https://fpga.mit.edu/6205/F22/labs/lab02). If you remember, we had a catsoop checker on the page that ran a testbench on your code, but it was a little unreliable and would often fail code that would actually work perfectly fine in hardware. This was our fault - our testbench didn't model how the keyboard worked completely corectly - but in this exercise we'll work around that by just yoinking data from the real world.

## Quick Blast to the Past

Here's a quick refresher on PS/2, lifted straight from the [lab02](https://fpga.mit.edu/6205/F22/labs/lab02#section_8) text:

PS/2 works by representing each character on the keyboard as a one-byte value from a predefined table, and sending that across the interface when a key is pressed.

Whoa whoa whoa, what does "sent" mean?

Basically, the PS/2 protocol runs over two connections / 'lines' between the device (i.e. your keyboard) and the PS/2 controller. The first of these connections is a clock, driven at a few kilohertz2 by the keyboard. The second of these connections is where the actual data flows. When the clock line drops from high to low, we can grab the value of the data line and store it for later use - eventually stacking up a full eight bits of information. This byte of information corresponds to a "scancode" in the above table, which maps to the character that you just pushed on your keyboard. However, as is often the case in communication of data, more than just the message must be sent in order to avoid ambiguity.

The transmission of an entire byte, therefore looks like the following: When you press down a key (or release a key...see below), you're gonna see the following happen:

- The clock line, which is high at idle time, is going to start ticking at its frequency of a few kilohertz. Meanwhile, a start bit, which signals the beginning of the transmission (and is always zero), is asserted on the data line. So at the first falling edge of the clock in a given sequence, you're going to see a 'zero' value asserted on the data line.
- The next eight falling clock edges will bring along 8 data bits, which contain the byte that represents the key you pressed.
- Next you'll see a parity bit, which is used for error checking. This uses the same method as you saw in pset 03. PS/2 uses odd parity which means if there are an even number of 1's in the 8 bits of the actual message a 1 is in the parity bit slot. If not, then a 0 is in the parity bit slot.
- Finally, you'll see a stop bit which is always a one. This signals the end of the transmission, and its receipt corresponds with the last falling clock edge you'll see until the next key is pressed.

For you visual folks, here's a quick diagram summarizing the above.

![](assets/ps2.jpeg)

## Adding a logic analyzer
Just like last time, we'll be configuring out `manta` instance with a configuration file called `manta.yaml`. There's a template in the starter code, go ahead and tweak it to add in a logic analyzer core according to the [documentatation](../logic_analyzer_core). There's a few parameters we'll want to pay close attention to:

- __Probes__: The signals we want to record. In our case, that's the PS/2 clock and data lines.
- __Sample Depth__: How many samples of them we want to record. In this particular configuration we can have up to ~64k samples, but transferring data is a little slow, so let's crank it down to 32k.
- __Triggers__: We want our capture to contain a valid PS/2 scancode, so we'll want to trigger when it starts transmitting it. What signal does what in order to begin the transaction?
- __Trigger Position__: Let's set this to 200 or so, so that we can make sure that our bus is idling properly before it starts sending data.

If you've got any questions about the configuration - let me know! Once you're happy with it, go ahead and generate the core, synthesize it, and flash the FPGA:

```
manta gen manta.yaml src/manta.v
vivado -mode batch -source build.tcl # or python3 lab-bc.py
openFPGALoader -b arty_a7_100t obj/out.bit
```

## Running the Logic Analyzer
Lovely! Now we'll want to run our core and __capture__ our signals. We'll throw these into a `.vcd` file, as well as a `.mem` file with the following:

```
manta capture manta.yaml my_logic_analyzer capture.vcd capture.mem
```

Assuming your config file is named `manta.yaml` and your logic analyzer core is named `my_logic_analyzer`. This will tell Manta that you'd like to run your logic analyzer, set the triggers, and wait for the trigger condition - you pressing a key on the keyboard. Once you do, the trigger will capture the signals, and your computer will read the data. Neato.

Go ahead and open the `caputure.vcd` file with `gtkwave capture.vcd`. This should look like our diagram from above! If it doesn't, lemme know.

## Onto something useful...
This is great! We can see our data and clock line, and it looks like what we expect. If we were working with something less standard than a PS2 keyboard, we could use Manta to double check that the signals received by the FPGA are the signals it expects.

Let's go one step farther - we're going to write a PS/2 decoder in Verilog (I know, I know it's been a while - I tried to pick something easy), but we're going to bypass the annoyness of setting up a testbench. Instead, we're just going to use the capture data we got from before, chunk that into our decoder, and see if we can get it to work in simulation. And once we do, we'll put our module on the FPGA, and see how we did.

## Playing Back Capture Data
There's a little bit of Verilog required to load our capture data from `capture.mem` into the simulation, but conveniently Manta will auto-generate this wrapper for you. If you run

```
manta playback manta.yaml my_logic_analyzer sim/playback.v
```

It'll create a module that outputs `ps2_clk` and `ps2_data`, and place it in `sim/playback.v`. There's an empty testbench in `sim/ps2_decoder_tb.sv`, go ahead and instantiate a copy of the playback module in the testbench. If you have a look at top of `sim/playback.v`, there's a little instantiation template you can copy-paste. Easy peasy.

While you're there, go ahead and instantiate a copy of ps2_decoder too, and wire it up to the output of the playback module.

## Writing ps2_decoder
Once you've got the plumbing all sorted, go ahead and type up the `ps2_decoder` module itself. VS Code should be installed on all the machines, and if you'd like to simulate with your captured data, just run:

```
iverilog -g2012 -o sim.out sim/ps2_decoder_tb.sv sim/playback.v src/ps2_decoder.sv
vvp sim.out
```

!!! tip

    Feel free to ignore the parity bit - just making sure that there's a start and stop bit is suffecient for the time being.


Make sure that the output of your `ps2_decoder` matches the key you pressed when you made the capture. Once you think you've got it working, feel free to throw it on the FPGA and build. The decoder is already instantiated in `top_level.sv`, so you shouldn't have to change anything outside of `ps2_decoder.v`.

Once you've got it working on hardware, congratulations!

## Debrief
We made something that worked right the first time, without spending a ton of time making a testbench beforehand. That's pretty cool. But it's got some big caveats:

- __It only tests the nominal case__: What if we received data whose parity bit didn't match? What if we only received 10 data bits intead of 11? We won't know how our ps2_decoder behaves in this case - we'd have to code those cases in manually, and Manta can't help us with that.

- __It requires hardware__: This is somewhat obvious, but we needed to have our FPGA and a PS/2 keyboard next to us before we ever started writing Verillog. That's not the most convenient thing - especially when PS/2 is simple enough to the point where I could probably write a PS/2 testbench in about the same amount of time it'd take to get the capture data into a simulation.

However, there were a few things that were pretty cool:

- __We had an exact representation of the nominal case__: If all data looks like our capture data did, we _know_ our design will work. That's powerful.
- __We didn't need to know what PS/2 looks like to start writing the simulation__: If this was your first time working with PS/2, this changes the development process from:
    - Understand PS/2.
    - Write PS/2 signal generator in testbench.
    - Write PS/2 decoder in testbench.

- and changes it to:
    - Import PS/2 signal generator to testbench.
    - Understand PS/2.
    - Write PS/2 decoder in testbench.

    And that might be useful, especially if you've got a device that you think is misbehaving. Being able to check it while you're writing your decoder is powerful.


Anyway, neither approach is perfect, and Manta's not meant to deliver something that is. It's meant to give you more options, all of which have tradeoffs.

That's about all I've got for now. Thanks for coming, and grab some pizza and stickers if you don't have some already :) Catch ya next week!
