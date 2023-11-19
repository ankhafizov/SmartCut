from glob import glob
from plugins.YOLO_based_detector.nms import non_max_suppression
import torch
import os
from natsort import natsorted
import onnxruntime as ort
import numpy as np
import cv2


def init_yolo_model():
    providers = (
        ["CUDAExecutionProvider", "CPUExecutionProvider"]
        if ort.get_device() == "GPU"
        else ["CPUExecutionProvider"]
    )
    session = ort.InferenceSession("YOLO_based_detector/weights/best.onnx", providers=providers)

    return session


def preprocess_img(image_path):
    img = cv2.imread(image_path)[:, :, ::-1]
    img = cv2.resize(np.array(img), (640, 640))
    img = np.expand_dims(img, -1)
    img = (np.transpose(img, (3, 2, 0, 1))) / 255.0
    img = img.astype(np.float32)

    return img


def process_chunk(session, unpacked_content_path, detect_class):
    detections = []
    times_sec = []

    for img_path in natsorted(glob(f"{unpacked_content_path}/*.jpg")):
        img = preprocess_img(img_path)
        outputs = session.run(['output0'], {"images": img})
        output = torch.from_numpy(outputs[0])
        out = non_max_suppression(prediction=output, conf_thres=0.7, iou_thres=0.5)

        detect = out[0][:, 5].cpu().detach().numpy()
        timestamp = int(os.path.basename(img_path)[:-4])

        if detect_class in detect:
            detections.append(1)
        else:
            detections.append(0)
        times_sec.append(timestamp)
        os.remove(img_path)

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
            sequences.append((start_index, i - 1))
            start_index = None
    if start_index is not None:
        sequences.append((start_index, len(lst) - 1))

    for start, stop in sequences:
        final_timestamps.append(
            {
                "start": timestamps[start] - (0 if timestamps[start] == 0 else 5),
                "stop": timestamps[stop],
            }
        )
    return final_timestamps
