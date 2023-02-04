import json
import yaml
from datetime import datetime
import os

# this works by taking a template file, parsing it for hooks, and then dropping in our spicy bits of verilog in those hooks.
# might update this later to just properly instantiate an ILA for us and we do this with parameters, but 
# the fundamental thing i care about is that systemverilog does not live in this file.

fpath = 'ila.json' # will update for argv soon!

with open(fpath, 'r') as f:
  config = json.load(f)

# make sure file is okay
assert config["probes"]
assert config["triggers"]
assert config["uart"] or config["ethernet"] # <- i have ideas hehe

def splice(source, find, replace):
  # find all instances of find in the source, and replace with replace
  #assert source.count(find) == 1
  return source.replace(find, replace)
  

with open('src/ila_template.sv', 'r') as t:
  ila_template = t.read()

# add timestamp and user
timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
ila_template = splice(ila_template, '@TIMESTAMP', timestamp);

user = os.environ.get('USER', os.environ.get('USERNAME'))
ila_template = splice(ila_template, '@USER', user);

# add trigger
trigger = [f'({trigger})' for trigger in config['triggers']]
trigger = ' || '.join(trigger)
ila_template = splice(ila_template, '@TRIGGER', trigger);

# add concat
concat = [name for name in config['probes']]
concat = ', '.join(concat)
concat = '{' + concat + '};'
ila_template = splice(ila_template, '@CONCAT', concat);

# add probes to ila module definition
probe_verilog = []
for name, width in config['probes'].items():
  if width == 1:
    probe_verilog.append(f'input wire {name},')

  else:
    probe_verilog.append(f'input wire [{width-1}:0] {name},')
  
probe_verilog = '\n\t'.join(probe_verilog)
ila_template = splice(ila_template, '@PROBES', probe_verilog);

# add sample width and depth
sample_width = sum([width for name, width in config['probes'].items()])
ila_template = splice(ila_template, '@SAMPLE_WIDTH', str(sample_width))
ila_template = splice(ila_template, '@SAMPLE_DEPTH', str(config['sample_depth']));

# add UART configuration
ila_template = splice(ila_template, '@DATA_WIDTH', str(int(config['uart']['data'])));
ila_template = splice(ila_template, '@BAUDRATE', str(config['uart']['baudrate']));
ila_template = splice(ila_template, '@CLK_FREQ_HZ', str(int(config['clock_freq'])));

# write output file
with open('src/ila.sv', 'w') as i:
  i.write(ila_template)