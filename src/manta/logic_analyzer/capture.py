from manta.logic_analyzer.playback import LogicAnalyzerPlayback
from manta.logic_analyzer import TriggerModes


class LogicAnalyzerCapture:
    """
    A container class for the data collected by a LogicAnalyzerCore. Contains
    methods for exporting the data as a VCD waveform file, a Python list, a
    CSV file, or a Verilog module.
    """

    def __init__(self, probes, trigger_location, trigger_mode, data):
        self._probes = probes
        self._trigger_location = trigger_location
        self._trigger_mode = trigger_mode
        self._data = data

        print(self._trigger_mode)

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
        """

        # Get index of probe with given name
        indicies = [i for i, p in enumerate(self._probes) if p.name == name]
        if len(indicies) == 0:
            raise ValueError(f"Probe {name} not found in LogicAnalyzerCapture!")

        if len(indicies) > 1:
            raise ValueError(
                f"Probe {name} found multiple times in LogicAnalyzerCapture!"
            )

        idx = indicies[0]

        # Sum up the widths of all the probes below this one
        lower = sum([len(p) for p in self._probes[:idx]])

        # Add the width of the probe we'd like
        upper = lower + len(self._probes[idx])

        total_probe_width = sum([len(p) for p in self._probes])
        binary = [f"{d:0{total_probe_width}b}" for d in self._data]
        return [int(b[lower:upper], 2) for b in binary]

    def export_csv(self, path):
        """
        Export the capture to a CSV file, containing the data of all probes in
        the core.
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
        Export the capture to a VCD file, containing the data of all probes in
        the core.
        """

        from vcd import VCDWriter
        from datetime import datetime

        # Use the same datetime format that iVerilog uses
        timestamp = datetime.now().strftime("%a %b %w %H:%M:%S %Y")
        vcd_file = open(path, "w")

        with VCDWriter(vcd_file, "10 ns", timestamp, "manta") as writer:
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
            for timestamp in range(0, 2 * len(self._data)):
                # Run the clock
                writer.change(clock, timestamp, timestamp % 2 == 0)

                # Set the trigger (if there is one)
                if self._trigger_mode == TriggerModes.SINGLE_SHOT:
                    triggered = (timestamp // 2) >= self._trigger_location
                    writer.change(trigger, timestamp, triggered)

                # Add other signals
                for signal in signals:
                    var = signal["var"]
                    sample = signal["data"][timestamp // 2]

                    writer.change(var, timestamp, sample)

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
