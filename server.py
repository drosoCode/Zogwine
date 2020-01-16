import flask
from flask import request, jsonify, abort, send_file, Response, stream_with_context
from flask_cors import CORS
from api import api
import requests

app = flask.Flask(__name__)
CORS(app)

app.config["DEBUG"] = True

api = api("config.json")
mp4FilePath = []

@app.route('/', methods=['GET'])
def home():
    return "<h1>API</h1>"

@app.route('/api/tvs/getEpisodes', methods=['GET'])
def getTVSEp():
    return jsonify(api.getTVSEp(request.args['idShow']))

@app.route('/api/tvs/getShows', methods=['GET'])
def getTVS():
    return jsonify(api.getTVSData())

@app.route('/api/tvs/setID', methods=['GET'])
def setTVSID():
    return jsonify(api.setTVSID(request.args['idShow'], request.args['id']))

@app.route('/api/tvs/runScan', methods=['GET'])
def runTVSScan():
    return jsonify({'status': "ok"})

@app.route('/api/tvs/fileInfos', methods=['GET'])
def getFileInfos():
    return jsonify(api.getFileInfos(request.args['idEpisode']))

@app.route('/api/tvs/getFile', methods=['GET'])
def getFile():
    ret = api.getFile(request.args['idEpisode'],request.args['token'])
    if ret[0]:
        global mp4FilePath
        mp4FilePath = ret[1]
        return jsonify({'status': 'ok', 'access': 'direct'})
    elif not ret[0] and ret[1]:
        return jsonify({'status': 'ok', 'access': 'transcoded'})
    else:
        return jsonify({'status': 'error'})

@app.route('/api/tvs/playbackEnd', methods=['GET'])
def getPlaybackEnd():
    #set as viewed for user, and stop transcoder if started
    return jsonify({'task': request.args['idEpisode'], "user":request.args['token']})

@app.route('/api/users/authenticate', methods=['GET','POST'])
def authenticateUser():
    #return user infos
    return jsonify({'response': api.authenticateUser(request.args['user'],request.args['password'])})

@app.route('/api/assets/transcoder/file')
def getTranscodedFile():
    req = requests.get(api.getTranscoderUrl()+"/file?name="+request.args['file']+"&user="+request.args['token'], stream = True)
    return Response(stream_with_context(req.iter_content(chunk_size=1024)), content_type = req.headers['content-type'])

@app.route('/api/assets/transcoder/list')
def getTranscodedFilesList():
    req = requests.get(api.getTranscoderUrl()+"/file?name=list&user="+request.args['token'], stream = True)
    return Response(stream_with_context(req.iter_content()), content_type = req.headers['content-type'])

@app.route('/api/assets/media')
def getMP4File():
    try:
        id = request.args['token']
        global mp4FilePath
        with open(mp4FilePath[id], 'rb') as bites:
            return send_file(bites.read(), attachment_filename='media.mp4', mimetype='video/mp4')
    except:
        abort(404)
