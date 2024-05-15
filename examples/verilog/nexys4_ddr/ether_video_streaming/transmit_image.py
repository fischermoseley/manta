import argparse
from PIL import Image
from manta import Manta

m = Manta("manta.yaml")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transmit an image to a networked FPGA")
    parser.add_argument("input_file", type=str, help="Path to input file")
    parser.add_argument("--width", type=int, default=128, help="Image width (optional)")
    parser.add_argument("--height", type=int, default=128, help="Image height (optional)")
    args = parser.parse_args()

    input_image = Image.open(args.input_file)
    resized_image = input_image.resize((args.width, args.height))

    for x in range(args.width):
        for y in range(args.height):
            r, g, b = resized_image.getpixel((x, y))

            r_4bit = r // 16
            g_4bit = g // 16
            b_4bit = b // 16

            addr = x + (y * 128)
            data = (r_4bit << 8) | (g_4bit << 4) | (b_4bit)
            print(addr, data)
            m.my_memory.write(addr, data)
