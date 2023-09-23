FROM python:3.9

COPY /common_utils /plugins/common_utils
COPY /ResNET_based_detector /plugins/ResNET_based_detector

WORKDIR /plugins
RUN pip3 install -r ResNET_based_detector/requirements.txt
RUN pip3 install -r common_utils/requirements.txt


CMD ["python", "ResNET_based_detector/main.py"]
# CMD ["python", "ResNET_based_detector/main.py", "kafka.bootstrap_servers=kafka:29092"]
# ENTRYPOINT ["tail", "-f", "/dev/null"]