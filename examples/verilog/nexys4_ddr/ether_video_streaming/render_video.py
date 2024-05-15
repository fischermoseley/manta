import argparse
import cv2
import numpy as np
from manta import Manta

m = Manta("manta.yaml")

def render_video(input_path, width=128, height=128):
    """
    Convert each frame in the input video to a 1D numpy array of the 12-bit
    pixel values that encode the frame. These can be directly written to
    Manta's memory core.

    Returns a 2D numpy array, indexed by [frame_number, pixel_address]
    """

    video = cv2.VideoCapture(input_path)

    if not video.isOpened():
        raise RuntimeError("Error: Could not open video file.")

    frames = []
    while video.isOpened():
        ret, frame = video.read()

        if ret:
            frames.append(frame_to_pixels(frame, width, height))

        else:
            break

    video.release()
    return frames

def frame_to_pixels(frame, width, height):
    """
    Resize a frame to the provided width and height, and return an array of the
    12-bit pixel colors at each location.

    Returns a 1D numpy array, representing a flattened frame.
    """

    resized_frame = cv2.resize(frame, (width, height))
    pixels = np.zeros(width * height, np.int16)

    for i in range(resized_frame.shape[0]):
        for j in range(resized_frame.shape[1]):
            b, g, r = resized_frame[i, j]

            # Convert to 12-bit color
            r_4bit = int(r // 16)
            g_4bit = int(g // 16)
            b_4bit = int(b // 16)

            addr = j + (i * width)
            pixels[addr] = (r_4bit << 8) | (g_4bit << 4) | (b_4bit)

    return pixels


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render a video to an array of flattened frames.")
    parser.add_argument("input_file", type=str, help="Path to input file")
    parser.add_argument("output_file", type=str, help="Path to output file")
    parser.add_argument("--width", type=int, default=128, help="Image width (optional)")
    parser.add_argument("--height", type=int, default=128, help="Image height (optional)")
    args = parser.parse_args()

    frames = render_video(args.input_file, args.width, args.height)
    np.save(args.output_file, frames)
