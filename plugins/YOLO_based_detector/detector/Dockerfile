FROM python:3.9
WORKDIR /scripts
COPY ./scripts .
RUN pip3 install kafka-python
CMD ["python", "detector.py"]


