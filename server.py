import flask
from flask import request, jsonify, abort, send_file, Response, stream_with_context, render_template
from flask_cors import CORS
import requests
import mimetypes
import os

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

@app.route('/api/logs')
def getServerLogs():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    if api.isAdmin(request.args['token']):
        return jsonify(getLogs(20))
    else:
        abort(403)
