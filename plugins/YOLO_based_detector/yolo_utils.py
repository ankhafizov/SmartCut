import torch

from plugins.common_utils.common_helpers import unzip_archive

def init_yolo_model():
    model = torch.hub.load("ultralytics/yolov5", "yolov5s")
    return model

def process_chunk(model, zipped_chank_path, detect_class, chunk_size):
 
    unpacked_content_path = zipped_chank_path
    chunk_num = int((zipped_chank_path.split('/')[-1]).split('.')[0])

    is_class_detected = False
    start_time = 0
    stop_time = 0
    detected_segments = []

    for idx, img in enumerate(os.listdir(unpacked_content_path)):
        detections = model(unpacked_content_path+'/'+img).pandas().xyxy[0]["name"].tolist()
        if detect_class in detections:
            print(idx)
            if not is_class_detected:
                start_time = chunk_num * chunk_size + idx
                is_class_detected = True

        if is_class_detected:# не распозналось но класс_детектед=тру - конец отрезка
            stop_time = chunk_num*chunk_size + idx
        else: # не распозналось и класс_детекдет = фолс - предыдущий тоже был пустой значит закрываем отрезок
            if start_time != 0 and stop_time != 0:
                detected_segments.append({"start": start_time, "stop": stop_time})
                start_time = 0
                stop_time = 0

    return detected_segments