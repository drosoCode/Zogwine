import flask
from flask import request, jsonify, abort, send_file, Response, stream_with_context
from flask_cors import CORS
import json
import base64
from subprocess import Popen, CREATE_NEW_CONSOLE
import signal
import os
import requests
import shutil

app = flask.Flask(__name__)
CORS(app)

app.config["DEBUG"] = True
userProcess = {}

with open("config.json") as f:
    config = json.load(f)

@app.route('/', methods=['GET'])
def home():
    return "<h1>API</h1>"

@app.route('/transcoder/file', methods=['GET'])
def getFile():
    name = request.args['name']
    token = request.args['token']
    #send transcoded file
    file = 'out/'+str(token)+'/'+name
    if os.path.exists(file):
        if '/' not in name and '/' not in token:
            return send_file(open(file, "rb"), mimetype='video/MP2T')
        else:
            abort(403)
    else:
        abort(404)

@app.route('/transcoder/start', methods=['GET'])
def runTranscode():
    token = request.args['token']
    subTxt = request.args['subTxt']
    audioStream = request.args['audioStream']
    subStream = request.args['subStream']

    path = '"' + config['tvsDirectory'] + '/' + base64.b64decode(request.args['file']).decode('utf-8') + '"'

    #remove old data in this dir, if it still exists
    if os.path.exists('out/'+token):
        try:
            shutil.rmtree('out/'+token)
        except:
            pass

    #recreate an empty out dir
    outFile = 'out/'+token
    if not os.path.exists(outFile):
        os.mkdir(outFile)
    outFile += '/stream'

    crf = str(config['crf']) #recommanded: 23
    hlsTime = str(config['hlsTime']) #in seconds
    
    if '..' not in path:
        if subStream != "-1":
            if subTxt == "1":
                cmd = " -hide_banner -loglevel error -vsync 0 -i " + path + " -pix_fmt yuv420p -vf subtitles=" + path.replace(":","\\\\:") +" -c:a aac -ar 48000 -b:a 128k -pix_fmt yuv420p -c:v h264_nvenc -map 0:a:" + audioStream + " -map 0:v:0 -map 0:s:" + subStream + " -crf " + crf + " -hls_time "+hlsTime+" -hls_playlist_type event -hls_segment_filename " + outFile + "%03d.ts " + outFile + ".m3u8"
            else:
                cmd = " -hide_banner -loglevel error -i " + path +" -pix_fmt yuv420p -preset medium -filter_complex \"[0:v][0:s:" + subStream + "]overlay[v]\" -map \"[v]\" -map 0:a:" + audioStream + " -c:a aac -ar 48000 -b:a 128k -c:v h264_nvenc -crf " + crf + " -hls_time "+hlsTime+" -hls_playlist_type event -hls_segment_filename " + outFile + "%03d.ts " + outFile + ".m3u8"
        else:
            cmd = " -hide_banner -loglevel error -vsync 0 -i " + path + " -pix_fmt yuv420p -c:a aac -ar 48000 -b:a 128k -pix_fmt yuv420p -c:v h264_nvenc -map 0:a:" + audioStream + " -map 0:v:0 -crf " + crf + " -hls_time "+str(hlsTime)+" -hls_playlist_type event -hls_segment_filename " + outFile + "%03d.ts " + outFile + ".m3u8"

        if os.name == 'nt':
            #windows
            cmd = 'ffmpeg.exe'+cmd
        else:
            cmd = './ffmpeg'+cmd


        print(cmd)
        #process = Popen(cmd, creationflags=CREATE_NEW_CONSOLE)
        process = Popen(cmd)
        userProcess[token] = process.pid

        return jsonify({'response':'ok'})
    else:
        abort(403)

@app.route('/transcoder/m3u8', methods=['GET'])
def getM3U8():
    file = 'out/'+str(request.args['token'])+'/stream.m3u8'
    if os.path.exists(file):
        return send_file(open(file, "rb"), mimetype='application/x-mpegURL')
    else:
        abort(404)

@app.route('/transcoder/stop', methods=['GET'])
def stop():
    try:
        token = request.args['token']
        if token in userProcess:
            os.kill(userProcess[token], signal.SIGTERM)
            del userProcess[token]
            
        if token != "":
            shutil.rmtree('out/'+token)
    except Exception as ex:
        print("Error: "+str(ex))
    
    return jsonify({'response':'ok'})

@app.route('/ping', methods=['GET'])
def ping():
    return 'pong'

@app.route('/transcoder/getHLSTime', methods=['GET'])
def getHLSTime():
    return jsonify({'response': config['hlsTime']})

app.run(host='0.0.0.0', port=8081)