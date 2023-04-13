import sys
from PIL import Image, ImageOps

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {0} <image to convert>".format(sys.argv[0]))

    else:
        input_fname = sys.argv[1]
        image_in = Image.open(input_fname)
        image_in = image_in.convert('RGB')

        num_colors_out = 256
        w, h = image_in.size
        print(f'Reducing {input_fname} of size {w}x{h} to {num_colors_out} unique colors.')

        # Take input image and divide each color channel's value by 16
        preview = image_in.copy()
        image_out = image_in.copy()

        for y in range(h):
            for x in range(w):
                r, g, b = image_in.getpixel((x, y))
                image_out.putpixel((x,y), (r//16, g//16, b//16))
                preview.putpixel((x,y), ((r//16)*16, (g//16)*16, (b//16)*16) )

        # Save the image preview
        preview.save('preview.png')
        print('Output image preview saved at preview.png')

        # Palettize the image
        image_out = image_out.convert(mode='P', palette=1, colors=num_colors_out)
        palette = image_out.getpalette()
        rgb_tuples = [tuple(palette[i:i+3]) for i in range(0, 3*num_colors_out, 3)]

        # Save pallete
        with open(f'palette.mem', 'w') as f:
            f.write( '\n'.join( [f'{r:01x}{g:01x}{b:01x}' for r, g, b in rgb_tuples] ) )

        print('Output image pallete saved at palette.mem')

        # Save the image itself
        with open(f'image.mem', 'w') as f:
            for y in range(h):
                for x in range(w):
                    f.write(f'{image_out.getpixel((x,y)):02x}\n')

        print('Output image saved at image.mem')