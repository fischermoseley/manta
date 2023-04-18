## Welcome back!
Howdy and welcome back to the party! Today's format is going to be a little different - we'll be splitting ya'll up into two groups and having one set test Manta, and one set test lab-bc 2.0 - in _parallel_. This will hopefully take less time, give us some more meaningful tests, and just be better on the whole. Hopefully this works, parallelization is kind of our _whole thing_.

## Update Manta:
There's been a fair bit of work since this time last week! Actually I'm curious how many commits there've been...

```
$ git log --since='1 week ago' | grep Fischer | wc -l

41
```

Oh god - we should definitely update Manta. And I should definitely, like, go outside or something. Go ahead and use the instructions on the [installation](../installation) page to get yourself up to date.

## Boilerplate
While you've got a terminal open, go ahead and grab the starter code from fischer's [super exclusive, boutique, and bouguie code hosting site](https://github.com/fischermoseley/tutorial_2_template)

## The fun part!
Today we'll be experimenting with the most Manta feature - the Logic Analyzer core. If we ever connected an ILA to your code last semester (or used a proper, benchtop logic analyzer like the ones on top the tables), then this will feel pretty familiar. But if not, perfect :)

The logic analyzer core connects to a set of singals that you want to investigate, which you do by _capturing_ them. When a _trigger condition_ is met, the logic analyzer core will record the value of each signal to internal memory, until that memory is full. That memory is then read back by the host machine, and exported to a `.vcd` file, which we can open in GTKWave and poke around with. And later, we'll "play back" that capture data in our own simulation, where we'll prototype a PS2 decoder. And if it works there on data captured from the real world, it should work just dandy in hardware.

We'll be kicking the tires on the Logic Analyzer core in the context of the PS/2 keyboards we used in [lab02](https://fpga.mit.edu/6205/F22/labs/lab02). If you remember, we had a catsoop checker on the page that ran a testbench on your code, but it was a little unreliable and would often fail code that would actually work perfectly fine in hardware. This was our fault - our testbench didn't model how the keyboard worked completely corectly - but in this exercise we'll work around that by just yoinking data from the real world.

## Quick Blast to the Past

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

Let's go one step farther - we're going to write a PS/2 decoder in Verilog (I know it's been a while, I tried to pick something easy), but we're going to bypass the annoyness of setting up a testbench. Instead, we're just going to use the capture data we got from before, chunk that into our decoder, and see if we can get it to work in simulation. And once we do, we'll chunk it on the FPGA, and see how we did.

# Debrief
- We made something that worked right the first time, without making a simulation beforehand. That's pretty cool. But it's got some caveats:
    - Helps catch only one quadrant of the should(n't) work/does work
    - Doesn't catch things that a normal simulation might. It only tests the nominal case. But it's an EXACT representation of the nominal case.
- This required us to have our FPGA next to us, and to test things in hardware. I could sit down, write a simulation in iverilog form scratch, and that'd be quicker than grabbing things from the real world. It's a tradeoff, and the purpose of Manta isn't to be a magic bullet - it's to give you more options.

