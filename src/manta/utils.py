import pkgutil
from math import ceil

def pack_16bit_words(data):
    """Takes a list of integers, interprets them as 16-bit integers, and
    concatenates them together in little-endian order."""

    for d in data:
        if d > 0: assert d < 2**16-1, "Unsigned integer too large."
        if d < 0: assert d < 2**15-1, "Signed integer too large."

    return int(''.join([f'{i:016b}' for i in data[::-1]]), 2)

def unpack_16bit_words(data, n_words):
    """Takes a integer, interprets it as a set of 16-bit integers
    concatenated together, and splits it into a list of 16-bit numbers"""

    assert isinstance(data, int), "Behavior is only defined for nonnegative integers."
    assert data >= 0, "Behavior is only defined for nonnegative integers."

    # convert to binary, split into 16-bit chunks, and then convert back to list of int
    binary = f'{data:0b}'.zfill(n_words * 16)
    return [int(binary[i:i+16], 2) for i in range(0, 16 * n_words, 16)][::-1]

class VerilogManipulator:
    def __init__(self, filepath=None):
        if filepath is not None:
            self.hdl = pkgutil.get_data(__name__, filepath).decode()

            # scrub any default_nettype or timescale directives from the source
            self.hdl = self.hdl.replace("`default_nettype none", "")
            self.hdl = self.hdl.replace("`default_nettype wire", "")
            self.hdl = self.hdl.replace("`timescale 1ns/1ps", "")
            self.hdl = self.hdl.strip()

            # python tries to be cute and automatically convert
            # line endings on Windows, but Manta's source comes
            # with (and injects) UNIX line endings, so Python
            # ends up adding way too many line breaks, so we just
            # undo anything it's done when we load the file
            self.hdl = self.hdl.replace("\r\n", "\n")

        else:
            self.hdl = None

    def sub(self, replace, find):
        # sometimes we have integer inputs, want to accomodate
        if isinstance(replace, str):
            replace_str = replace

        elif isinstance(replace, int):
            replace_str = str(replace)

        else:
            raise ValueError("Only string and integer arguments supported.")


        # if the string being subbed in isn't multiline, just
        # find-and-replace like normal:
        if "\n" not in replace_str:
            self.hdl = self.hdl.replace(find, replace_str)

        # if the string being substituted in is multiline,
        # make sure the replace text gets put at the same
        # indentation level by adding whitespace to left
        # of the line.
        else:
            for line in self.hdl.split("\n"):
                if find in line:
                    # get whitespace that's on the left side of the line
                    whitespace = line.rstrip().replace(line.lstrip(), "")

                    # add it to every line, except the first
                    replace_as_lines = replace_str.split("\n")
                    replace_with_whitespace = f"\n{whitespace}".join(replace_as_lines)

                    # replace the first occurance in the HDL with it
                    self.hdl = self.hdl.replace(find, replace_with_whitespace, 1)

    def get_hdl(self):
        return self.hdl

    def net_dec(self, nets, net_type, trailing_comma = False):
        """Takes a dictonary of nets in the format {probe: width}, and generates
        the net declarations that would go in a Verilog module definition.

        For example, calling net_dec({foo : 1, bar : 4}, "input wire") would produce:

        input wire foo,
        input [3:0] wire bar

        Which you'd then slap into your module declaration, along with all the other
        inputs and outputs the module needs."""

        dec = []
        for name, width in nets.items():
            if width == 1:
                dec.append(f"{net_type} {name}")

            else:
                dec.append(f"{net_type} [{width-1}:0] {name}")

        dec = ",\n".join(dec)
        dec = dec + "," if trailing_comma else dec
        return dec

    def net_conn(self, nets, trailing_comma = False):
        """Takes a dictionary of nets in the format {probe: width}, and generates
        the net connections that would go in the Verilog module instantiation.

        For example, calling net_conn({foo: 1, bar: 4}) would produce:

        .foo(foo),
        .bar(bar)

        Which you'd then slap into your module instantiation, along with all the other
        module inputs and outputs that get connected elsewhere."""


        conn = [f".{name}({name})" for name in nets]
        conn = ",\n".join(conn)
        conn = conn + "," if trailing_comma else conn

        return conn