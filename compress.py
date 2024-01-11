import os
from multiprocessing import Process, Manager, cpu_count
import time
import sys
import cv2
from PIL import Image
import fpstimer
import zlib
import zstd



ASCII_CHARS = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", " "]
frame_size = 237

ASCII_LIST = []
STORE_ON_DISK = False

#video_fps = ""
global video_fps      

def get_video_fps(video_path):
    capture = cv2.VideoCapture(video_path)
    fps = capture.get(cv2.CAP_PROP_FPS)
    capture.release()
    return fps

def extract_transform_generate(video_path, start_frame, end_frame, shared_list, frame_size):
     # Initialize shared list with empty strings for frames in the specified range
    #for i in range(start_frame - 1, end_frame):
    #    shared_list[i] = ""
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
            ascii_characters = pixels_to_ascii(greyscale(resize_image(image)))  # get ascii characters
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


# Resize image
def resize_image(image_frame):
    width, height = image_frame.size
    aspect_ratio = height / float(width * 2)  # 2.5 modifier to offset vertical scaling on console
    new_height = int(aspect_ratio * frame_size)
    resized_image = image_frame.resize((frame_size, new_height))
    # print('Aspect ratio: %f' % aspect_ratio)
    # print('New dimensions %d %d' % resized_image.size)
    return resized_image


# Greyscale
def greyscale(image_frame):
    return image_frame.convert("L")


# Convert pixels to ascii
def pixels_to_ascii(image_frame):
    pixels = image_frame.getdata()
    characters = "".join([ASCII_CHARS[pixel // 25] for pixel in pixels])
    return characters


# Open image => Resize => Greyscale => Convert to ASCII => Store in memory => Store in text file
def ascii_generator(image_path, start_frame, number_of_frames):
    ascii_images = []

    # Calculate the delay for each frame based on the desired output FPS
    frame_delay = 1 / video_fps

    for current_frame in range(start_frame, number_of_frames + 1):
        path_to_image = f"{image_path}/BadApple_{current_frame}.jpg"
        image = Image.open(path_to_image)
        
        ascii_characters = pixels_to_ascii(greyscale(resize_image(image)))
        
        pixel_count = len(ascii_characters)
        ascii_image = "\n".join(
            [ascii_characters[index:(index + frame_size)] for index in range(0, pixel_count, frame_size)]
        )
        ascii_images.append(ascii_image)

    if STORE_ON_DISK:
        for idx, ascii_img in enumerate(ascii_images, start=start_frame):
            file_name = f"TextFiles/bad_apple{idx}.txt"
            try:
                with open(file_name, "w", encoding='UTF-8') as f:
                    f.write(ascii_img)
            except FileNotFoundError:
                continue
            time.sleep(frame_delay)  # Introduce delay for desired output FPS



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

def rle_encode(data):
    encoding = ''
    prev_char = ''
    count = 1

    if not data: return ''

    for char in data:
        # If the prev and current characters
        # don't match...
        if char != prev_char:
            # ...then add the count and character
            # to our encoding
            if prev_char:
                encoding += str(count) + prev_char
            count = 1
            prev_char = char
        else:
            # Or increment our counter
            # if the characters do match
            count += 1
    else:
        # Finish off the encoding
        encoding += str(count) + prev_char
        return encoding

def rle_decode(data):
    decode = ''
    count = ''
    for char in data:
        # If the character is numerical...
        if char.isdigit():
            # ...append it to our count
            count += char
        else:
            # Otherwise we've seen a non-numerical
            # character and need to expand it for
            # the decoding
            decode += char * int(count)
            count = ''
    return decode


MODE = 0
def main():
    print("What's your video url (youtube)?")
    a = input("URL [e.g. https://www.youtube.com/watch?v=FtutLA63Cp8]: ")
    print("Run the command { yt-dlp -o file_to_encode.mp4 -f \"[height <=? 480]\" " + a + " }")
    input("Press enter once done")
    start_time = time.time()
    user_input = "file_to_encode.mp4"  # For testing purposes, you can uncomment the input prompt line
    video_fps = get_video_fps(user_input)
    print("Encoding...")
    cap = cv2.VideoCapture(user_input)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if MODE == 0:
    
        total_frames = preflight_operations(user_input)
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"{elapsed} seconds taken for generation, {(elapsed / total_frames)*1000}ms per frame")
        print("Converting to string object")
        """
        with open("data.txt", 'w') as f:
            f.write('\n'.join(ASCII_LIST))
        """
        print("Compressing...")
        compressed = compress(5, '\n'.join(ASCII_LIST))
        with open("compressed_data.zstd", "wb") as f:
            f.write(compressed)
    


def compress(algo: int, indata: str):
    compression_functions = {
        1: lambda data: rle_encode(data),
        2: lambda data: zlib.compress(data.encode(), level=-1),
        3: lambda data: zlib.compress(data.encode(), level=9),
        4: lambda data: zstd.compress(data.encode(), 3),
        5: lambda data: zstd.compress(data.encode(), 22),
    }

    compression_function = compression_functions.get(algo, lambda data: data)
    return compression_function(indata)

def decompress(algo: int, indata: bytes):
    compression_functions = {
        1: lambda data: rle_decode(data),
        2: lambda data: zlib.decompress(data),
        3: lambda data: zlib.decompress(data),
        4: lambda data: zstd.decompress(data),
        5: lambda data: zstd.decompress(data),
    }

    compression_function = compression_functions.get(algo, lambda data: data)
    return compression_function(indata)

if __name__ == "__main__":
    main()
    


# Old testing stuff
"""
    print("Compression Type | Size   | Time to decompress")
    print(f"None             |{round(len(ascii_str)/(1024**2), 2)}mb | 0.0")
    

    ascii_rle = rle_encode(ascii_str)
    start_t = time.time()
    rle_decode(ascii_rle)
    end_t = time.time()
    print(f"RLE              | {round(len(ascii_rle)/(1024**2), 2)}mB | {end_t - start_t}")
    
    
    ascii_zlib = zlib.compress(ascii_str.encode(), level=-1)
    start_t = time.time()
    zlib.decompress(ascii_zlib)
    end_t = time.time()
    print(f"Zlib 6           | {round(len(ascii_zlib)/(1024**2), 2)}mB | {end_t - start_t}")

    ascii_zlib = zlib.compress(ascii_str.encode(), level=9)
    start_t = time.time()
    zlib.decompress(ascii_zlib)
    end_t = time.time()
    print(f"Zlib 9           | {round(len(ascii_zlib)/(1024**2), 2)}mB | {end_t - start_t}")
    
    ascii_zstd = zstd.compress(ascii_str.encode(), 3)
    start_t = time.time()
    zstd.decompress(ascii_zstd)
    end_t = time.time()
    print(f"zstd 3           | {round(len(ascii_zlib)/(1024**2), 2)}mB | {end_t - start_t}")
    
    
    ascii_zstd = zstd.compress(ascii_str.encode(), 22)
    start_t = time.time()
    zstd.decompress(ascii_zstd)
    end_t = time.time()
    print(f"zstd 22          | {round(len(ascii_zlib)/(1024**2), 2)}mB | {end_t - start_t}")
    """
    
"""
1: python3 compress.py - default mp4
            Mean        Std.Dev.    Min         Median      Max
real        19.187      0.444       18.897      19.047      20.461      
user        112.626     0.671       112.043     112.372     114.339     
sys         1.741       0.032       1.697       1.739       1.793       
(base) [ghostdog@ghostdog badapple]$ 


1: python3 compress.py - huffyuv
            Mean        Std.Dev.    Min         Median      Max
real        20.100      0.894       19.691      19.799      22.765      
user        122.062     0.485       120.897     122.048     122.791     
sys         3.175       0.537       2.739       2.942       4.496  


ffmpeg -i fearanddelight.mp4 -f rawvideo -pixel_format bgr24 out.test.mkv

"""