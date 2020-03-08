FROM jrottenberg/ffmpeg:4.1-nvidia 

WORKDIR /home/server
COPY . .

RUN \
    apt-get update && apt-get install -y python3 python3-pip libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev\
    && pip3 install --no-cache-dir -r requirements.txt \
    && chmod +x start.sh main.py

CMD "/home/start.sh"