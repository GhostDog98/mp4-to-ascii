import os
from multiprocessing import Process, Manager, cpu_count
import time
import sys
import cv2
from PIL import Image
import fpstimer

import zstd
import zstandard


ASCII_CHARS = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", " "]
frame_size = 237

ASCII_LIST = []
STORE_ON_DISK = False

global video_fps      


def extract_transform_generate(video_path, start_frame, end_frame, shared_list, frame_size):
     # Initialize shared list with empty strings for frames in the specified range
    shared_list[0:] = ["" for aa in shared_list[0:]]
    capture = cv2.VideoCapture(video_path)
    capture.set(1, start_frame)  # Points cap to target frame
    current_frame = start_frame
    frame_count = 1
    ret, image_frame = capture.read()
    
    while ret and current_frame <= end_frame:
        ret, image_frame = capture.read()
        
        try:
            image = Image.fromarray(image_frame)
            #ascii_characters = pixels_to_ascii(image)
            
            ######################################################################
            #                  CONVERT PIXELS TO ASCII
            ######################################################################
            # Convert to grayscale
            image_frame = image_frame.convert("L")
            
            # Resize
            width, height = image_frame.size
            aspect_ratio = height / float(width * 2) 
            new_height = int(aspect_ratio * frame_size)
            image_frame = image_frame.resize((frame_size, new_height))
            
            # Convert to ascii
            pixels = image_frame.getdata()
            ascii_characters = "".join([ASCII_CHARS[pixel // 25] for pixel in pixels])
            
            pixel_count = len(ascii_characters)
            ascii_image = "\n".join(
                [ascii_characters[index:(index + frame_size)] for index in range(0, pixel_count, frame_size)])

            # Append the ASCII frame at the correct index in the shared list
            shared_list[current_frame - 1] = ascii_image

        # For god knows what reason, running this codes `fromarray` line
        # causes it to throw an AttributeError that can be ignored...
        except AttributeError:
            continue

        frame_count += 1  # increases internal frame counter
        current_frame += 1  # increases global frame counter

    capture.release()


def preflight_operations(path):
    if os.path.exists(path):
        path_to_video = path.strip()
        cap = cv2.VideoCapture(path_to_video)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        manager = Manager()
        shared_list = manager.list(["" for _ in range(total_frames)])
        processes = []


        total_threads = int(cpu_count() / 3)
        frames_per_process = total_frames // total_threads

        for i in range(total_threads):
            start_frame = i * frames_per_process + 1
            end_frame = (i + 1) * frames_per_process if i < 3 else total_frames - 1
            process = Process(target=extract_transform_generate,
                      args=(path_to_video, start_frame, end_frame, shared_list, frame_size))
            processes.append(process)
            process.start()

        for process in processes:
            process.join()

        ASCII_LIST.extend(shared_list)
        sys.stdout.write('ASCII generation completed!\n')

        return total_frames  # Return total frames
    
    # Otherwise, if we cant find the file
    sys.stdout.write('Warning: File not found!\n')
    return -1



MODE = 0
def main():
    """
    print("What's your video url (youtube)?")
    a = input("URL [e.g. https://www.youtube.com/watch?v=FtutLA63Cp8]: ")
    print("Run the command { yt-dlp -o file_to_encode.mp4 -f \"[height <=? 480]\" " + a + " && \
          ffmpeg -i file_to_encode.mp4 -vcodec copy -an f.mp4 && \
          rm file_to_encode.mp4 && \
          mv f.mp4 file_to_encode.mp4 }")
    input("Press enter once done")
    """
    start_time = time.time()
    user_input = "file_to_encode.mp4"  
    
    
    # Get the fps
    capture = cv2.VideoCapture(user_input)
    video_fps = capture.get(cv2.CAP_PROP_FPS)
    capture.release()
    
    #print("Encoding...")
    cap = cv2.VideoCapture(user_input)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if MODE == 0:
    
        total_frames = preflight_operations(user_input)
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"{elapsed} seconds taken for generation, {(elapsed / total_frames)*1000}ms per frame")
     #   print("Converting to string object")
        
        with open("data.txt", 'w') as f:
            f.write('\n'.join(ASCII_LIST))
        print("Compressing...")
        start_time = time.time()
        compressed = zstd.compress('\n'.join(ASCII_LIST).encode(), 22)
        end_time = time.time()
        print("Non threaded compression took", (end_time - start_time))
        
        start_time = time.time()
        ctxx = zstandard.ZstdCompressor(22, threads=4)
        compressed = ctxx.compress('\n'.join(ASCII_LIST).encode())
        end_time = time.time()
        print("Threaded compression took", (end_time - start_time))
        with open("compressed_data.zstd", "wb") as f:
            f.write(compressed)
        


if __name__ == "__main__":
    main()
