FROM jrottenberg/ffmpeg:4.1-nvidia1804

ENTRYPOINT []

WORKDIR /home/server
ADD ./requirements.txt ./requirements.txt

ENV LD_LIBRARY_PATH=  
RUN apt-get update && apt-get install -y python3.8 python3.8-distutils python3.8-dev libssl-dev libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev locales libxml2-dev nginx iputils-ping curl
ENV LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib64:/usr/lib:/usr/lib64:/lib:/lib64"
ENV C_INCLUDE_PATH="/usr/include/libxml2/"

ENV PYTHON python3.8
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.8 get-pip.py && rm get-pip.py && pip install --no-cache-dir -r requirements.txt

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ADD nginx.conf /etc/nginx

CMD "bash"
