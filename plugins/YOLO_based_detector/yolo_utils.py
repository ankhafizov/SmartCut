from glob import glob
import torch
import os
import logging
from natsort import natsorted
from plugins.common_utils.common_helpers import unzip_archive

def init_yolo_model():
    model = torch.hub.load("ultralytics/yolov5", "yolov5s")
    return model

def process_chunk(model, zipped_chunks_path, detect_class):

    unpacked_content_path =  unzip_archive(zipped_chunks_path)

    detections = []
    times_sec = []


    for  img in natsorted(glob(f"{unpacked_content_path}/*.jpg")):

        detections = model(img).pandas().xyxy[0]["name"].tolist()
        timestamp = int(os.path.basename(img)[:-4])

        if detect_class in detections:
            detections.append(1)
        else:
            detections.append(0)
        times_sec.append(timestamp)
        
    return detections, times_sec


def merge_timestamps(lst, timestamps):
    sequences = []
    final_timestamps = []
    start_index = None
    
    for i in range(len(lst)):
        if lst[i] == 1:
            if start_index is None:
                start_index = i
        elif start_index is not None:
            sequences.append((start_index, i-1))
            start_index = None
    if start_index is not None:
        sequences.append((start_index, len(lst)-1))
        
    for start, stop in sequences:
        final_timestamps.append({'start': timestamps[start], 'stop': timestamps[stop]})
    return final_timestamps
