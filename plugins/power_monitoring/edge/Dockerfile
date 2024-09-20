FROM python:3.9-slim

WORKDIR /app

COPY daemon.py /app/
COPY utils.py /app/
COPY requirements.txt /app/
COPY imagenet_classes.txt /app/

RUN pip install -r /app/requirements.txt

RUN mkdir /app/uploads

EXPOSE 8080

ENTRYPOINT [ "python", "-u", "/app/daemon.py"]