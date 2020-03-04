import flask
from flask import request, jsonify, abort, send_file, Response, stream_with_context, render_template
from flask_cors import CORS
import requests
import mimetypes
import os

from log import getLogs
from api import api as apiClass
api = apiClass("config.json")

app = flask.Flask(__name__)
CORS(app)

app.config["DEBUG"] = True

lastRequestedFile = {}

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/api/tvs/getEpisodes', methods=['GET'])
def getTVSEp():
    return jsonify(api.getTVSEp(request.args['idShow']))

@app.route('/api/tvs/getShows', methods=['GET'])
def getTVS():
    return jsonify(api.getTVSData(False))

@app.route('/api/tvs/getShowsMultipleResults', methods=['GET'])
def getTVSMR():
    return jsonify(api.getTVSData(True))

@app.route('/api/tvs/setID', methods=['GET'])
def setTVSID():
    if api.isAdmin(request.args['token']):
        return jsonify(api.setTVSID(request.args['idShow'], request.args['id']))
    else:
        abort(401)

@app.route('/api/tvs/runScan', methods=['GET'])
def runTVSScan():
    api.runScan()
    return jsonify({'status': "ok"})

@app.route('/api/tvs/fileInfos', methods=['GET'])
def getFileInfos():
    return jsonify(api.getFileInfos(request.args['idEpisode']))

@app.route('/api/tvs/playbackEnd', methods=['GET'])
def playbackEnd():
    #set as viewed for user, and stop transcoder if started
    t = request.args['token']
    api.stopTranscoder(t, lastRequestedFile)
    s = True
    if t in lastRequestedFile:
        s = api.setViewedTime(request.args['idEpisode'], t, lastRequestedFile[t])
        del lastRequestedFile[s]
    return jsonify({'response':s})

@app.route('/api/tvs/setViewed', methods=['GET'])
def setViewed():
    #set episode as viewed for user
    s = api.setViewed(request.args['idEpisode'], request.args['token'])
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
    return jsonify(api.getUserData(request.args['token']))


@app.route('/api/transcoder/start')
def startTranscoder():
    s = api.startTranscoder(request.args['idEpisode'], request.args['token'], request.args['audioStream'], request.args['subStream'], request.args['subTxt'])
    if s:
        return jsonify({'response':'ok'})
    else:
        abort(403)

@app.route('/api/transcoder/m3u8')
def getTranscoderM3U8():
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
    name = request.args['name']
    token = request.args['token']
    lastRequestedFile[token] = name
    #send transcoded file
    file = 'out/'+str(token)+'/'+name
    if os.path.exists(file):
        if '/' not in name and '/' not in token:
            return send_file(open(file, "rb"), mimetype='video/MP2T')
        else:
            abort(403)
    else:
        abort(404)

@app.route('/api/tvs/getFile')
def getFile():
    path = api.getEpPath(request.args['idEpisode'])
    if os.path.exists(path):
        mime = mimetypes.guess_type(path, strict=False)[0]
        if 'video' in mime:
            return send_file(open(path, "rb"), mimetype=mime)
        else:
            abort(404)
    else:
        abort(404)

@app.route('/api/logs')
def getServerLogs():
    if api.isAdmin(request.args['token']):
        return jsonify(getLogs(20))
    else:
        abort(401)

@app.route('/ping', methods=['GET'])
def ping():
    return 'pong'
