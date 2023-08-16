import sys
from PIL import Image, ImageOps

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {0} <image to convert>".format(sys.argv[0]))

    else:
        input_fname = sys.argv[1]
        image_in = Image.open(input_fname)
        image_in = image_in.convert('RGB')

        # Resize the image
        image_in = image_in.resize((128, 128))
        image_out = image_in.copy()
        w, h = image_in.size

        # Take input image and divide each color channel's value by 16
        for y in range(h):
            for x in range(w):
                r, g, b = image_in.getpixel((x, y))
                image_out.putpixel((x,y), (r//16, g//16, b//16))


        # Save the image itself
        pixels = []
        for y in range(h):
            for x in range(w):
                (r, g, b) = image_out.getpixel((x,y))
                color = (r*16*16) + (g*16) + (b)
                pixels.append(color)

        from manta import Manta
        m = Manta('manta.yaml')

        addrs = list(range(len(pixels)))
        m.image_mem.write(addrs, pixels)