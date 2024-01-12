#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 23:35:55 2024

@author: ghostdog
"""
from PIL import Image, ImageOps
import time
import numpy as np



print("Method             | Time per item    | Total Time of Bad Apple")

test_frame = np.load("test_image_frame.npy")
testnum = 10000
start_time = time.time()
for i in range(testnum):
    image = Image.fromarray(test_frame)
    image.convert('L')
end_time = time.time()
elapsed = end_time - start_time
average_time_per_iteration = elapsed / testnum
average_time_per_iteration_ms = average_time_per_iteration * 1000  # Convert to nanoseconds
print(f"image.convert('L') | {round(average_time_per_iteration_ms, 3)}ms          | {round(average_time_per_iteration_ms*6000)}ms")

start_time = time.time()
for i in range(testnum):
    image = Image.fromarray(test_frame)
    ImageOps.grayscale(image)
end_time = time.time()
elapsed = end_time - start_time
average_time_per_iteration = elapsed / testnum
average_time_per_iteration_ms = average_time_per_iteration * 1000  # Convert to nanoseconds
print(f"imageOps.grayscale | {round(average_time_per_iteration_ms, 3)}ms          | {round(average_time_per_iteration_ms*6000)}ms")

start_time = time.time()
for i in range(testnum):
    grayscale_image = np.dot(test_frame[..., :3], [0.299, 0.587, 0.114])
    np.squeeze(grayscale_image)
end_time = time.time()
elapsed = end_time - start_time
average_time_per_iteration = elapsed / testnum
average_time_per_iteration_ms = average_time_per_iteration * 1000  # Convert to nanoseconds
print(f"Numpy dot          | {round(average_time_per_iteration_ms, 3)}ms          | {round(average_time_per_iteration_ms*6000)}ms")

