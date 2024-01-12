import fpstimer
import zstd


FRAME_SIZE = 237


def main():
    # Read file
    with open("compressed_data.zstd", 'rb') as f:
        compressed_data = f.read()
        
    # Decompress data and re-assmble into blocks
    data = zstd.decompress(compressed_data).decode()
    data = data.split('\n')
    # Assume 30 fps
    timer = fpstimer.FPSTimer(30)
    # Now lets play
    num_lines = len(data)
    lines_per_chunk = 66
    characters_per_line = FRAME_SIZE
    
    for i in range(0, num_lines, lines_per_chunk):
        chunk = data[i:i + lines_per_chunk]  # Extract a chunk of 45 lines
        print('\033[2J')
        for line in chunk:
            print(line[:characters_per_line])  # Print 150 characters per line
        timer.sleep()  # Wait 1/30 of a second


if __name__ == "__main__":
    main()
