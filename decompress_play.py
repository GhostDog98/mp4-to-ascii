import zlib
import fpstimer
import zstd

FRAME_SIZE = 238

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


def decompress(algo: int, indata: bytes):
    compression_functions = {
        1: rle_decode,
        2: zlib.decompress,
        3: zlib.decompress,
        4: zstd.decompress,
        5: zstd.decompress,
    }

    compression_function = compression_functions.get(algo, lambda data: data)
    return compression_function(indata)

import os, psutil
def main():
    
    
    parent_pid = os.getppid()
    if psutil.Process(parent_pid).name() == 'Powershell.exe':
        print("Running in powershell, changing clear cmd")
        clr = 'Clear-Host'
    else:
        clr = '\033[2J'
    
    with open("compressed_data.zstd", 'rb') as f:
        data = decompress(5, f.read()).decode()
        data = data.split('\n')
    # Assume 30 fps
    timer = fpstimer.FPSTimer(30)
    # Now lets play
    #lines = data.split('\n')  # Split the decompressed data into lines
    num_lines = len(data)
    lines_per_chunk = 66
    characters_per_line = FRAME_SIZE
    
    for i in range(0, num_lines, lines_per_chunk):
        chunk = data[i:i + lines_per_chunk]  # Extract a chunk of 45 lines
        print(clr)
        for line in chunk:
            print(line[:characters_per_line])  # Print 150 characters per line
        timer.sleep()  # Wait 1/30 of a second


if __name__ == "__main__":
    main()
