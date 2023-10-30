from glob import glob
import torch
import os
from natsort import natsorted

def init_yolo_model():
    model = torch.hub.load("ultralytics/yolov5", "yolov5s")
    model.conf=0.6
    return model

def process_chunk(model, unpacked_content_path, detect_class):


    detections = []
    times_sec = []


    for  img in natsorted(glob(f"{unpacked_content_path}/*.jpg")):

        detect = model(img).pandas().xyxy[0]["name"].tolist()
        timestamp = int(os.path.basename(img)[:-4])

        if detect_class in detect:
            detections.append(1)
        else:
            detections.append(0)
        times_sec.append(timestamp)
        os.remove(img)
        
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
        final_timestamps.append({'start': timestamps[start] - (0 if timestamps[start]==0 else 5 ), 'stop': timestamps[stop]})
    return final_timestamps
