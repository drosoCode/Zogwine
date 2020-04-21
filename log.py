import logging
from logging.handlers import RotatingFileHandler

logFile = 'out/debug.log'

def getLogger():    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

    file_handler = RotatingFileHandler(logFile, 'a', 1000000, 0, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    #stream_handler.setLevel(logging.DEBUG)
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)
    return logger

def getLogs(lines=10):
    with open(logFile, encoding='utf-8') as f:
        content = f.read().splitlines()
    count = len(content)
    data = []
    for i in range(count-lines,count):
        data.append(content[i])
    return data

logger = getLogger()