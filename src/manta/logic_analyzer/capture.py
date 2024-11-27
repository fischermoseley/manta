import math
from datetime import datetime

from vcd import VCDWriter

from manta.logic_analyzer.fsm import TriggerModes
from manta.logic_analyzer.playback import LogicAnalyzerPlayback
from manta.utils import *


class LogicAnalyzerCapture:
    """
    A container class for the data collected by a LogicAnalyzerCore. Contains
    methods for exporting the data as a VCD waveform file, a Python list, a
    CSV file, or a Verilog module.
    """

    def __init__(self, probes, trigger_location, trigger_mode, data, interface):
        self._probes = probes
        self._trigger_location = trigger_location
        self._trigger_mode = trigger_mode
        self._data = data
        self._interface = interface

    def get_trigger_location(self):
        """
        Returns the location of the trigger in the capture. This will match the
        value of "trigger_location" provided in the configuration file at the
        time of capture.
        """

        return self._trigger_location

    def get_trace(self, name):
        """
        Gets the value of a single probe over the capture.

        Args:
            name (str): The name of the probe.

        Returns:
            data (List[int]): The value of the probe at every timestep,
                interpreted as an unsigned integer. Has length equal to
                the `sample_depth` of the core that produced the capture.
        """

        # Get index of probe with given name
        indices = [i for i, p in enumerate(self._probes) if p.name == name]
        if len(indices) == 0:
            raise ValueError(f"Probe {name} not found in LogicAnalyzerCapture!")

        if len(indices) > 1:
            raise ValueError(
                f"Probe {name} found multiple times in LogicAnalyzerCapture!"
            )

        idx = indices[0]

        # Sum up the widths of all the probes below this one
        lower = sum([len(p) for p in self._probes[:idx]])

        # Add the width of the probe we'd like
        upper = lower + len(self._probes[idx])

        total_probe_width = sum([len(p) for p in self._probes])
        binary = [f"{d:0{total_probe_width}b}" for d in self._data]
        return [int(b[lower:upper], 2) for b in binary]

    def export_csv(self, path):
        """
        Export the capture to a CSV file.

        Args:
            path (str): Path to the destination file.

        Returns:
            None
        """

        names = [p.name for p in self._probes]
        values = [self.get_trace(n) for n in names]

        # Transpose list of lists so that data flows top-to-bottom instead of
        # left-to-right
        values_transpose = [list(x) for x in zip(*values)]

        import csv

        with open(path, "w") as f:
            writer = csv.writer(f)

            writer.writerow(names)
            writer.writerows(values_transpose)

    def export_vcd(self, path):
        """
        Export the capture to a VCD file.

        Args:
            path (str): Path to the destination file.

        Returns:
            None
        """

        # Compute the timescale from the frequency of the provided clock
        half_period = 1 / (2 * self._interface.clock_freq)
        exponent = math.floor(math.log10(half_period))
        exponent_eng = (exponent // 3) * 3

        # The VCD file format specification supports no units larger or smaller
        # than these
        units = {
            0: "s",
            -3: "ms",
            -6: "us",
            -9: "ns",
            -12: "ps",
            -15: "fs",
        }

        timescale_unit = units[exponent_eng]
        timescale_exponent = 10 ** (exponent - exponent_eng)
        timescale_exact = half_period / (10**exponent)
        timescale_integer = round(timescale_exact)

        if abs(timescale_exact - timescale_integer) > 1e-3:
            warn("VCD file timescale will differ slightly from exact clock frequency.")

        timescale = (timescale_exponent, timescale_unit)

        # Use the same datetime format that iVerilog uses
        timestamp = datetime.now().strftime("%a %b %w %H:%M:%S %Y")
        vcd_file = open(path, "w")

        with VCDWriter(vcd_file, timescale, timestamp, "manta") as writer:
            # Each probe has a name, width, and writer associated with it
            signals = []
            for p in self._probes:
                signal = {
                    "name": p.name,
                    "width": len(p),
                    "data": self.get_trace(p.name),
                    "var": writer.register_var("manta", p.name, "wire", size=len(p)),
                }
                signals.append(signal)

            clock = writer.register_var("manta", "clk", "wire", size=1)

            # Include a trigger signal such would be meaningful (ie, we didn't trigger immediately)
            if self._trigger_mode == TriggerModes.SINGLE_SHOT:
                trigger = writer.register_var("manta", "trigger", "wire", size=1)

            # Add the data to each probe in the vcd file
            for sample_index in range(0, 2 * len(self._data)):
                sample_timestamp = timescale_integer * sample_index

                # Run the clock
                writer.change(clock, sample_timestamp, sample_index % 2 == 0)

                # Set the trigger (if there is one)
                if self._trigger_mode == TriggerModes.SINGLE_SHOT:
                    triggered = (sample_index // 2) >= self._trigger_location
                    writer.change(trigger, sample_timestamp, triggered)

                # Add other signals
                for signal in signals:
                    var = signal["var"]
                    sample = signal["data"][sample_index // 2]

                    writer.change(var, sample_timestamp, sample)

        vcd_file.close()

    def get_playback_module(self):
        """
        Returns an Amaranth module that will playback the captured data. This
        module is synthesizable, so it may be used in either simulation or
        on the FPGA directly by including it your build process.
        """

        return LogicAnalyzerPlayback(self._probes, self._data)

    def export_playback_verilog(self, path):
        """
        Exports a Verilog module that will playback the captured data. This
        module is synthesizable, so it may be used in either simulation or
        on the FPGA directly by including it your build process.
        """

        lap = self.get_playback_module()
        from amaranth.back import verilog

        with open(path, "w") as f:
            f.write(
                verilog.convert(
                    lap,
                    name="logic_analyzer_playback",
                    ports=lap.get_top_level_ports(),
                    strip_internal_attrs=True,
                )
            )
