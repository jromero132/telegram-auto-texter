FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ="Europe/Stockholm"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /telegram-auto-texter
ADD . .
RUN pip install -r requirements.txt
CMD ["python3", "-u", "main.py"]
