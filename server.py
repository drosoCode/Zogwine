import flask
from flask import request, jsonify, abort, send_file, Response, stream_with_context, render_template
from flask_cors import CORS
from api import api as apiClass
import requests

app = flask.Flask(__name__)
CORS(app)

app.config["DEBUG"] = True

api = apiClass("config.json")
mp4FilePath = []

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

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
    requests.get(api.getTranscoderUrl()+"/stop?token="+request.args['token'])
    return jsonify({'task': request.args['idEpisode'], "user":request.args['token']})

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

@app.route('/api/assets/transcoder/file')
def getTranscodedFile():
    file = request.args['file']
    if '/' not in file:
        req = requests.get(api.getTranscoderUrl()+"/file?name="+file+"&token="+request.args['token']+"&subTxt="+str(request.args['subTxt'])+"&audioStream="+str(request.args['audioStream'])+"&subStream="+str(request.args['subStream']), stream = True)
        return Response(stream_with_context(req.iter_content(chunk_size=1024)), content_type = req.headers['content-type'])
    else:
        return jsonify({'response':'error'})

@app.route('/api/assets/transcoder/list')
def getTranscodedFilesList():
    data = generateM3U8(requests.get(api.getTranscoderUrl()+"/file?name=list&token="+request.args['token']).text)
    return data

@app.route('/api/assets/media')
def getMP4File():
    try:
        id = request.args['token']
        global mp4FilePath
        with open(mp4FilePath[id], 'rb') as bites:
            return send_file(bites.read(), attachment_filename='media.mp4', mimetype='video/mp4')
    except:
        abort(404)

@app.route('/ping', methods=['GET'])
def ping():
    return 'pong'

def generateM3U8(files):
    return files