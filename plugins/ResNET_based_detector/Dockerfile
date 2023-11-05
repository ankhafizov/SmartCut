FROM python:3.9

RUN pip3 install --upgrade pip
RUN pip3 install hydra-core
RUN pip3 install scipy
RUN pip3 install natsort
RUN pip3 install pillow
RUN pip3 install onnxruntime

COPY /common_utils /plugins/common_utils
COPY /ResNET_based_detector /plugins/ResNET_based_detector

WORKDIR /plugins
RUN pip3 install -r ResNET_based_detector/requirements.txt
RUN pip3 install -r common_utils/requirements.txt

CMD ["sh", "-c", "python ResNET_based_detector/main.py kafka.bootstrap_servers=${bootstrap_servers}"]
# ENTRYPOINT ["tail", "-f", "/dev/null"]