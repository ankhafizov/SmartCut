import torch
import os
import logging
from plugins.common_utils.common_helpers import unzip_archive

def init_yolo_model():
    model = torch.hub.load("ultralytics/yolov5", "yolov5s")
    return model

def process_chunk(model, zipped_chunks_path, detect_class, chunk_size):

    unpacked_content_path =  unzip_archive(zipped_chunks_path)

    detected_segments = {}

    for idx, img in enumerate(os.listdir(unpacked_content_path)):
        detections = model(unpacked_content_path+'/'+img).pandas().xyxy[0]["name"].tolist()
        if detect_class in detections:
            detected_segments[int(img[:-4])]=1
        else:
            detected_segments[int(img[:-4])]=0
        
    return detected_segments

def merge_timestamps(timestamps_dict):   

    myKeys = list(timestamps_dict.keys())
    myKeys.sort()
    sorted_dict = {i: timestamps_dict[i] for i in myKeys}

    merged_results = []
    start=0
    end=0
    prev=-1
    for k,v in sorted_dict.items():
        if v==1 and prev!=1:
            start=k
            prev=v
        elif v==0:
            end=k
            merged_results.append({'start': start, 'end': end})
            prev=v

    return merged_results
