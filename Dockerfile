FROM jrottenberg/ffmpeg:4.1-nvidia 

WORKDIR /home/server
COPY . .

RUN \
    apt-get update && apt-get install -y python3 python-pip3 \
    && pip install --no-cache-dir -r requirements.txt \
    && chmod +x start.sh main.py

CMD "/home/start.sh"