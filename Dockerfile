FROM jrottenberg/ffmpeg:4.1-nvidia 

ENTRYPOINT []

WORKDIR /home/server
COPY . .

RUN apt-get update && apt-get install -y python3 python3-pip libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev
RUN pip3 install --no-cache-dir -r requirements.txt && chmod +x start.sh main.py

RUN apt-get update && apt-get install -y locales && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

CMD "./start.sh"