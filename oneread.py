import concurrent.futures
import cv2
import time
import numpy as np
from PIL import Image
from multiprocessing import Manager, Lock, RawArray
import zstandard

ASCII_CHARS = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", " "]
ASCII_CHAR_LEN = len(ASCII_CHARS)
frame_size = 237

class Threader:
    def __init__(self, ascii_list, receive_messages, lock):
        self.ascii_list = ascii_list
        self.receive_messages = receive_messages
        self.lock = lock

    def process_frame_batch(self, frames, frame_size):
        if self.receive_messages:
            ascii_frames = []
            for frame in frames:
                image = Image.fromarray(frame)

                # Convert to grayscale
                image_frame_pixels = image.convert("L")

                # Resize while maintaining the aspect ratio
                new_width = frame_size
                new_height = int((frame_size / float(image_frame_pixels.width)) * image_frame_pixels.height)
                image_frame_pixels = image_frame_pixels.resize((new_width, new_height))

                pixels = np.array(image_frame_pixels)

                # Convert to ASCII characters using NumPy
                ascii_characters = np.array(ASCII_CHARS)[np.clip((pixels // (256 // ASCII_CHAR_LEN)), 0, ASCII_CHAR_LEN - 1)].flatten()

                # Ensure the final ASCII frame has the correct width
                final_frame_width = min(frame_size, new_width)
                ascii_frame = "".join(ascii_characters)[:final_frame_width]

                ascii_frames.append(ascii_frame)

            with self.lock:
                self.ascii_list.extend(ascii_frames)

def main():
    start_time = time.time()
    manager = Manager()
    lock = Lock()

    receive_messages = True

    path = "file_to_encode.mp4"
    cap = cv2.VideoCapture(path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Create a shared list to store ASCII frames
    ascii_list = manager.list()

    threader = Threader(ascii_list, receive_messages, lock)

    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        ret, frame = cap.read()
        frames_batch = []

        while ret:
            frames_batch.append(frame)
            if len(frames_batch) == 10:  # Adjust batch size as needed
                executor.submit(threader.process_frame_batch, frames_batch, frame_size)
                frames_batch = []
            ret, frame = cap.read()

        # Process any remaining frames
        if frames_batch:
            executor.submit(threader.process_frame_batch, frames_batch, frame_size)

    # Now ascii_list contains the processed ASCII frames in order
    ascii_result = "".join(ascii_list)

    print("Elapsed time is ", time.time() - start_time)

    with open("test.txt", 'w') as f:
        f.write(ascii_result)

    # Now ascii_result contains the processed ASCII frames in order
    ctxx = zstandard.ZstdCompressor(3, threads=12)
    compressed = ctxx.compress(ascii_result.encode())
    with open("compressed_data.zstd", "wb") as f:
        f.write(compressed)

if __name__ == "__main__":
    main()
