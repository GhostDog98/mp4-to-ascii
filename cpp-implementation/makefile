CXX = g++
CXXFLAGS = -std=c++17 -O3 -march=native -fprofile-use -funroll-all-loops -ftree-vectorize -funsafe-math-optimizations -march=native -flto -mtune=native -fopenmp -DNDEBUG $(shell pkg-config --cflags opencv4)
LDFLAGS = $(shell pkg-config --libs opencv4) -lopencv_core -lopencv_highgui -lzstd

SRC = main.cpp

all: mp4-to-ascii

mp4-to-ascii: $(SRC)
	$(CXX) $(CXXFLAGS) $(SRC) -o $@ $(LDFLAGS)

clean:
	rm -f mp4-to-ascii
	rm -f compressed_data.zstd
	rm -f file_to_encode.mp4
	rm -f file.txt

