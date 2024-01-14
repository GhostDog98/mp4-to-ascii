// Copyright [2024] Lilly ***REMOVED***
// Licensed under the GNU GPL v3.
// If needed under a different license, please contact the author.
/*
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>. 
*/
#include <zstd.h>
#include <thread>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <opencv2/opencv.hpp>

#include <boost/algorithm/string/join.hpp>

const int ASCII_CHAR_LEN = 11;
const int frame_size = 237;

std::vector<std::string> ASCII_LIST;
std::string path = "file_to_encode.mp4";
bool STORE_ON_DISK = false;
double video_fps;

// Function to extract frames from video, convert to ASCII, and store in shared_list
void extract_transform_generate(const std::string& video_path, int start_frame, int end_frame,
                                std::vector<std::string>& shared_list, int frame_size) {
    cv::VideoCapture capture(video_path);
    capture.set(cv::CAP_PROP_POS_FRAMES, start_frame);
    int current_frame = start_frame;

    cv::Mat image_frame;
    bool ret = capture.read(image_frame);

    while (ret && current_frame <= end_frame) {
        try {
            cv::Mat image;
            cv::cvtColor(image_frame, image, cv::COLOR_BGR2GRAY);
            cv::resize(image, image, cv::Size(frame_size, frame_size));

            std::string ascii_image;
            for (int i = 0; i < frame_size; ++i) {
                std::string ascii_characters;
                for (int j = 0; j < frame_size; ++j) {
                    int pixel = static_cast<int>(image.at<uchar>(i, j));
                    // Ensure pixel value is within the correct range
                    pixel = std::max(0, std::min(pixel, 255));
                    ascii_characters += "@#S%?*+;:, "[pixel / 25];
                }
                ascii_image += ascii_characters + '\n';
            }

            shared_list[current_frame - 1] = ascii_image;
        } catch (cv::Exception& e) {
            // Handle exception if needed
            continue;
        }

        ++current_frame;
        ret = capture.read(image_frame);
    }

    capture.release();
}

// Optimized version of extract_transform_generate using iterators and reserved space
void extract_transform_generate_optimized(const std::string& video_path, int start_frame, int end_frame, std::vector<std::string>& shared_list, int frame_size) {
    cv::VideoCapture capture(video_path);
    capture.set(cv::CAP_PROP_POS_FRAMES, start_frame);
    int current_frame = start_frame;

    cv::Mat image_frame;
    bool ret = capture.read(image_frame);

    while (ret && current_frame <= end_frame) {
        try {
            cv::resize(image_frame, image_frame, cv::Size(frame_size, frame_size));

            std::string ascii_image;
            ascii_image.reserve(frame_size * (frame_size + 1));  // Reserve space for efficiency

            for (int i = 0; i < frame_size; ++i) {
                std::back_insert_iterator<std::string> it = std::back_inserter(ascii_image);
                for (int j = 0; j < frame_size; ++j) {
                    int pixel = static_cast<int>(image_frame.at<cv::Vec3b>(i, j)[0]);
                    // Ensure pixel value is within the correct range
                    pixel = std::max(0, std::min(pixel, 255));
                    *it = "@#S%?*+;:, "[pixel / 25];
                }
                *it = '\n';
            }

            shared_list[current_frame - 1] = std::move(ascii_image);
        } catch (cv::Exception& e) {
            // Handle exception if needed
            continue;
        }

        ++current_frame;
        ret = capture.read(image_frame);
    }

    capture.release();
}



// Function to compress ASCII data using Zstd and save to compressed_data.zstd
void zstd_compress(std::vector<std::string> ASCII) {
    std::cout << "Compressing..." << std::endl;
    ZSTD_CCtx* ctx = ZSTD_createCCtx();
    std::string compressed_data = boost::algorithm::join(ASCII, "\n");
    size_t compressed_size = ZSTD_compressBound(compressed_data.size());
    std::vector<char> compressed(compressed_size);
    compressed_size = ZSTD_compressCCtx(ctx, compressed.data(), compressed.size(),
                                        compressed_data.data(), compressed_data.size(), 3);
    ZSTD_freeCCtx(ctx);

    std::ofstream compressed_file("compressed_data.zstd", std::ios::binary);
    compressed_file.write(compressed.data(), compressed_size);
    compressed_file.close();
}

// Function to get video from YouTube and process it
void get_video() {
    std::string video_url;
    std::cout << "Video URL [Default https://www.youtube.com/watch?v=FtutLA63Cp8]: ";
    std::getline(std::cin, video_url);
    video_url = video_url.empty() ? "https://www.youtube.com/watch?v=FtutLA63Cp8" : video_url;

    // yt-dlp -o file_to_encode.mp4 -f "[height <=? 480]"  https://www.youtube.com/watch?v=FtutLA63Cp8 && ffmpeg -i file_to_encode.mp4 -vcodec copy -an f.mp4 && rm file_to_encode.mp4 && mv f.mp4 file_to_encode.mp4
    std::string command = "yt-dlp -o file_to_encode.mp4 -f \"[height <=? 480]\" " + video_url +
                          " && ffmpeg -i file_to_encode.mp4 -vcodec copy -an f.mp4 && " +
                          "rm file_to_encode.mp4 && mv f.mp4 file_to_encode.mp4";
    std::cout << "Running command..." << std::endl;
    system(command.c_str());
}

// Function to get the total frames in the video
int get_video_fps() {
    cv::VideoCapture cap(path);
    int frames_num = static_cast<int>(cap.get(cv::CAP_PROP_FRAME_COUNT));
    cap.release();
    return frames_num;
}

int main() {
    // Get the video from YouTube
    //get_video();

    // Start timer
    double start_time = cv::getTickCount();

    int total_frames = get_video_fps();

    std::vector<std::string> shared_list(total_frames, "");
    std::vector<std::thread> threads;

    int total_threads = 4;
    int frames_per_process = total_frames / total_threads;

    // Launch threads for frame processing
    for (int i = 0; i < total_threads; ++i) {
        int start_frame = i * frames_per_process + 1;
        int end_frame = (i < 3) ? (i + 1) * frames_per_process : total_frames - 1;
        threads.emplace_back(extract_transform_generate_optimized, path, start_frame, end_frame,
                             std::ref(shared_list), frame_size);
    }

    // Wait for all threads to finish
    for (auto& thread : threads) {
        thread.join();
    }

    // Combine results from threads
    ASCII_LIST.insert(ASCII_LIST.end(), shared_list.begin(), shared_list.end());

    // Stop timer and calculate elapsed time
    double end_time = cv::getTickCount();
    double elapsed = (end_time - start_time) / cv::getTickFrequency();
    //std::cout << elapsed << " seconds taken for generation, " << (elapsed / total_frames) * 1000 << "ms per frame" << std::endl;
    std::cout << elapsed << "," << (elapsed / total_frames) * 1000 << std::endl;

    // Save ASCII art to file.txt
    std::ofstream file("file.txt");
    file << boost::algorithm::join(ASCII_LIST, "\n");
    file.close();

    // Compress to a zstd file
    //zstd_compress(ASCII_LIST);

    return 0;
}
