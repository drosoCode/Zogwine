import flask
from flask import request, jsonify, abort, send_file, Response, stream_with_context
from flask_cors import CORS
import json
import base64
from subprocess import Popen, CREATE_NEW_CONSOLE
import signal
import os
import requests

app = flask.Flask(__name__)
CORS(app)

app.config["DEBUG"] = True
userProcess = {}

with open("config.json") as f:
    config = json.load(f)

@app.route('/', methods=['GET'])
def home():
    return "<h1>API</h1>"

@app.route('/file', methods=['GET'])
def getFile():
    name = request.args['name']
    token = request.args['token']
    if name == 'list':
        #list transcoded files
        files = []
        for item in os.listdir(config['tvsDirectory'] + '/' + str(token)):
            extension = item[item.rfind('.')+1:]
            if extension == 'ts':
                files.append(item)

        return jsonify({'response':files})
    else:
        #send transcoded file
        file = config['tvsDirectory']+'/'+str(token)+'/'+name
        with open(file , 'rb') as bites:
            return send_file(bites.read(), attachment_filename=name, mimetype='video/mp4')

@app.route('/transcode', methods=['GET'])
def runTranscode():
    token = request.args['token']
    file = config['tvsDirectory'] + base64.b64decode(request.args['file'])
    subTxt = request.args['subTxt']
    audioStream = request.args['audioStream']
    subStream = request.args['subStream']

    outFile = 'transcoded'
    crf = '23'
    
    if '/' not in file:
        file = '"' + file + '"'
        if subTxt:
            cmd = config['ffmpeg']+" -hide_banner -loglevel error -vsync 0 -i " + file + " -pix_fmt yuv420p -vf subtitles=" + file +" -c:a aac -ar 48000 -b:a 128k -pix_fmt yuv420p -c:v h264_nvenc -map 0:a:" + audioStream + " -map 0:v:0 -map 0:s:" + subStream + " -crf " + crf + " -hls_time 60 -hls_playlist_type event -hls_segment_filename " + outFile + "%03d.ts " + outFile + ".m3u8"
        else:
            cmd = config['ffmpeg']+" -hide_banner -loglevel error -i " + file +" -pix_fmt yuv420p -preset medium -filter_complex \"[0:v][0:s:" + subStream + "]overlay[v]\" -map \"[v]\" -map 0:a:" + audioStream + " -c:a aac -ar 48000 -b:a 128k -c:v h264_nvenc -crf " + crf + " -hls_time 120 -hls_playlist_type event -hls_segment_filename " + outFile + "%03d.ts " + outFile + ".m3u8"
        
        if os.name != 'nt':
            #not windows
            cmd = './'+cmd

        process = Popen(cmd, creationflags=CREATE_NEW_CONSOLE)
        userProcess[token] = process.pid

        return jsonify({'response':'ok'})
    else:
        return jsonify({'response':'error'})

@app.route('/stop', methods=['GET'])
def stop():
    token = request.args['token']
    if token in userProcess:
        os.kill(userProcess[token], signal.SIGTERM)
        del userProcess[token]

    return jsonify({'response':'ok'})

@app.route('/ping', methods=['GET'])
def ping():
    return 'pong'


app.run(host='0.0.0.0')