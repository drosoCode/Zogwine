import flask
from flask import request, jsonify, abort, send_file, Response, stream_with_context, render_template
from flask_cors import CORS
import requests
import mimetypes
import os
import re

from log import getLogs
from api import api as apiClass
api = apiClass("config/config.json")

app = flask.Flask(__name__)
CORS(app)

app.config["DEBUG"] = True

lastRequestedFile = {}

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/api/tvs/getEpisodes', methods=['GET'])
def getTVSEp():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.getTVSEp(request.args['idShow']))

@app.route('/api/tvs/getShows', methods=['GET'])
def getTVS():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.getTVSData(False))

@app.route('/api/tvs/getShowsMultipleResults', methods=['GET'])
def getTVSMR():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.getTVSData(True))

@app.route('/api/tvs/setID', methods=['GET'])
def setTVSID():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    if api.isAdmin(request.args['token']):
        return jsonify(api.setTVSID(request.args['idShow'], request.args['id']))
    else:
        abort(401)

@app.route('/api/tvs/runScan', methods=['GET'])
def runTVSScan():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    if not api.isAdmin(request.args['token']):
        abort(403)
    api.runScan()
    return jsonify({'status': "ok"})

@app.route('/api/tvs/fileInfos', methods=['GET'])
def getFileInfos():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.getFileInfos(request.args['idEpisode']))

@app.route('/api/tvs/playbackEnd', methods=['GET'])
def playbackEnd():
    t = request.args['token']
    if not api.checkToken(t):
        abort(401)
    #set as viewed for user, and stop transcoder if started
    api.stopTranscoder(t)
    s = True
    if t in lastRequestedFile:
        s = api.setViewedTime(request.args['idEpisode'], t, lastRequestedFile[t])
        del lastRequestedFile[t]
    return jsonify({'response':s})

@app.route('/api/tvs/toggleViewed', methods=['GET'])
def toggleViewed():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    #set episode as viewed for user
    s = api.toggleViewed(request.args['idEpisode'], request.args['token'])
    return jsonify({'response':s})

@app.route('/api/users/authenticate', methods=['GET','POST'])
def authenticateUser():
    #return user infos
    d = api.authenticateUser(request.args['user'],request.args['password'])
    if not d:
        abort(401)
    else:
        return jsonify({'response': d})

@app.route('/api/users/data', methods=['GET','POST'])
def getUserData():
    #return user infos
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.getUserData(request.args['token']))


@app.route('/api/transcoder/start')
def startTranscoder():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    s = api.startTranscoder(request.args['idEpisode'], request.args['token'], request.args['audioStream'], request.args['subStream'], request.args['subTxt'])
    if s:
        return jsonify({'response':'ok'})
    else:
        abort(403)

@app.route('/api/transcoder/m3u8')
def getTranscoderM3U8():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    token = request.args['token']
    fileUrl = "/api/transcoder/file?token="+token+"&name="
    dat = ''

    file = 'out/'+str(token)+'/stream.m3u8'
    if os.path.exists(file):
        fileData = open(file, "r").read()
        for i in fileData.split("\n"):
            if ".ts" in i and "stream" in i:
                dat += fileUrl+i+"\n"
            else:
                dat += i+"\n"
        return Response(dat, mimetype='application/x-mpegURL')
    else:
        abort(404)

@app.route('/api/transcoder/file')
def getTranscoderFile():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    name = request.args['name']
    token = request.args['token']
    lastRequestedFile[token] = name
    #send transcoded file
    file = 'out/'+str(token)+'/'+name
    if os.path.exists(file):
        if '/' not in name and '/' not in token:
            return send_file(open(file, "rb"), mimetype='video/MP2T', as_attachment=True, attachment_filename=file[file.rfind('/')+1:])
        else:
            abort(403)
    else:
        abort(404)

@app.route('/api/tvs/getFile')
def getFile():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    path = api.getEpPath(request.args['idEpisode'])
    if os.path.exists(path):
        mime = mimetypes.guess_type(path, strict=False)[0]
        if 'video' in mime:
            return send_file(open(path, "rb"), mimetype=mime, as_attachment=True, attachment_filename=path[path.rfind('/')+1:])
        else:
            abort(404)
    else:
        abort(404)

def get_chunk(full_path, byte1=None, byte2=None):
    file_size = os.stat(full_path).st_size
    start = 0
    length = 102400

    if byte1 < file_size:
        start = byte1
    if byte2:
        length = byte2 + 1 - byte1
    else:
        length = file_size - start

    with open(full_path, 'rb') as f:
        f.seek(start)
        chunk = f.read(length)
    return chunk, start, length, file_size

@app.route('/api/tvs/streamFile')
def streamFile():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)

    path = api.getEpPath(request.args['idEpisode'])
    if os.path.exists(path):
        mime = mimetypes.guess_type(path, strict=False)[0]
        if mime in ['video/mp4', 'video/mpeg']:
                range_header = request.headers.get('Range', None)
                byte1, byte2 = 0, None
                if range_header:
                    match = re.search(r'(\d+)-(\d*)', range_header)
                    groups = match.groups()

                    if groups[0]:
                        byte1 = int(groups[0])
                    if groups[1]:
                        byte2 = int(groups[1])

                chunk, start, length, file_size = get_chunk(path, byte1, byte2)
                resp = Response(chunk, 206, mimetype=mime, content_type=mime, direct_passthrough=True)
                resp.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(start, start + length - 1, file_size))
                resp.headers.add('Accept-Ranges', 'bytes')
                return resp
        else:
            abort(404)
    else:
        abort(404)

@app.route('/api/logs')
def getServerLogs():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    if api.isAdmin(request.args['token']):
        return jsonify(getLogs(20))
    else:
        abort(403)
