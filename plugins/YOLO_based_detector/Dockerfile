FROM python:3.9

COPY /common_utils /plugins/common_utils
COPY /YOLO_based_detector /plugins/YOLO_based_detector

WORKDIR /plugins
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN pip3 install -r YOLO_based_detector/requirements.txt
RUN pip3 install -r common_utils/requirements.txt

CMD ["sh", "-c", "python YOLO_based_detector/main.py kafka.bootstrap_servers=${bootstrap_servers}"]



