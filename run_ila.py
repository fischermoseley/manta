from sys import argv
import json
import serial
from vcd import VCDWriter
from datetime import datetime

def check_config(config):
   """Check that configuration is okay"""
   assert config["probes"]
   assert config["triggers"]
   assert config["uart"]

def setup_serial(ser, config):
   ser.baudrate = config['uart']['baudrate']
   ser.port = config['uart']['port']
   ser.timeout = config['uart']['timeout']

   # setup number of data bits
   if config['uart']['data'] == 8:
      ser.bytesize = serial.EIGHTBITS

   elif config['uart']['data'] == 7:
      ser.bytesize = serial.SEVENBITS

   elif config['uart']['data'] == 6:
      ser.bytesize = serial.SIXBITS

   elif config['uart']['data'] == 5:
      ser.bytesize = serial.FIVEBITS

   else:
      raise ValueError("Invalid number of data bits in UART configuration.")

   # setup number of stop bits
   if config['uart']['stop'] == 1:
      ser.stopbits = serial.STOPBITS_ONE

   elif config['uart']['stop'] == 1.5:
      ser.stopbits = serial.STOPBITS_ONE_POINT_FIVE

   elif config['uart']['stop'] == 2:
      ser.stopbits = serial.STOPBITS_TWO

   else:
      raise ValueError("Invalid number of stop bits in UART configuration.")

   # setup parity
   if config['uart']['parity'] == 'none':
      ser.parity = serial.PARITY_NONE

   elif config['uart']['parity'] == 'even':
      ser.parity = serial.PARITY_EVEN

   elif config['uart']['parity'] == 'odd':
      ser.parity = serial.PARITY_ODD

   elif config['uart']['parity'] == 'mark':
      ser.parity = serial.PARITY_MARK

   elif config['uart']['parity'] == 'space':
      ser.parity = serial.PARITY_SPACE

   else:
      raise ValueError("Invalid parity setting in UART configuration.")

def part_select(data, width):
    top, bottom = width

    assert top >= bottom

    mask = 2**(top - bottom + 1) - 1
    return (data >> bottom) & mask

def make_widths(config):
   # {probe0, probe1, probe2}
   # [12, 1, 3] should produce
   # [ (11,0) , (12, 12), (15,13) ]

   widths = list(config['probes'].values())

   parts = []
   for i, width in enumerate(widths):
      if (i == 0):
         parts.append( (width - 1, 0) )

      else:
         parts.append( ((parts[i-1][1] + width) , (parts[i-1][1] + 1)) )

   # reversing this list is a little bit of a hack, should fix/document
   return parts[::-1]


## Main Program

# parse args
if len(argv) == 1 or argv[1] == '-h':
   print("""
   run_ila.py: interface with the ILA on the FPGA, setting triggers and downlinking waveform data.
   usage: python3 run_ila.py [config input file] [vcd output file]
   options:
      -h: print this help menu
      -l: list all available serial devices

   example: python3 run_ila.py ila.json ila.vcd
   """)
   exit()

elif argv[1] == '-l':
   import serial.tools.list_ports

   for info in serial.tools.list_ports.comports():
      print(info)

elif len(argv) == 2:
   config_fpath = argv[1]
   vcd_fpath = 'ila.vcd'
   

elif len(argv) == 3:
   config_fpath = argv[1]
   vcd_fpath = argv[2]

else:
   exit()

# read config
with open(config_fpath, 'r') as f:
  config = json.load(f)

# obtain bytestream from FPGA
with serial.Serial() as ser:
   setup_serial(ser, config)
   ser.open()
   ser.flushInput()
   ser.write(b'\x30')
   data = ser.read(4096)

# export VCD
vcd_file = open(vcd_fpath, 'w')
timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

with VCDWriter(vcd_file, timescale='10 ns', date=timestamp, version = 'openILA') as writer:

   # add probes to vcd file
   vcd_probes = []
   for name, width in config['probes'].items():
      probe = writer.register_var('ila', name, 'wire', size = width)
      vcd_probes.append(probe)

   # calculate bit widths for part selecting
   widths = make_widths(config)

   # slice data, and dump to vcd file
   for timestamp, value in enumerate(data):
      for probe_num, probe in enumerate(vcd_probes):
         val = part_select(value, widths[probe_num])
         writer.change(probe, timestamp, val)

vcd_file.close()