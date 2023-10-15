FROM python:3.9

RUN pip3 install torch
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN pip3 install --upgrade pip
RUN pip3 install torchvision
RUN pip3 install hydra-core
RUN pip3 install opencv-python
RUN pip3 install scipy
RUN pip3 install natsort
RUN pip3 install ultralytics
RUN pip3 install kafka-python



COPY /common_utils /plugins/common_utils
COPY /YOLO_based_detector /plugins/YOLO_based_detector

WORKDIR /plugins
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN pip3 install -r YOLO_based_detector/requirements.txt
RUN pip3 install -r common_utils/requirements.txt

CMD ["sh", "-c", "python YOLO_based_detector/main.py kafka.bootstrap_servers=${bootstrap_servers}"]



