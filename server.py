import flask
from flask import request, jsonify, abort, send_file, Response, stream_with_context, render_template, redirect
from flask_cors import CORS
import requests
import mimetypes
import os
import re
from base64 import b64decode
import time

from log import getLogs
from api import api as apiClass
api = apiClass("config/config_dev.json")

app = flask.Flask(__name__)
CORS(app)

app.config["DEBUG"] = True

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


################################################################ MAIN ##################################################################

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

def getFile(path, requiredMime):
    mime = mimetypes.guess_type(path, strict=False)[0]
    if requiredMime in mime:
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
            resp.headers.add('Content-Disposition', 'attachment', filename=path[path.rfind('/')+1:])
            return resp
    else:
        abort(404)

@app.route('/api/core/getStatistics')
def getStats():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return api.getStatistics(request.args['token'])

@app.route('/api/core/getLogs')
def getServerLogs():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    if api.isAdmin(request.args['token']):
        try:
            l = int(request.args['amount'])
        except Exception:
            l = 20
        return jsonify(getLogs(l))
    else:
        abort(403)

@app.route('/cache/image')
def getImage():
    id = request.args['id']
    url = b64decode(id).decode()
    file = 'out/cache/'+id
    ext = url[url.rfind('.')+1:]
    mime = 'image/'+ext
    if ext == 'jpg':
        mime = 'image/jpeg'
        
    if '/' not in id and os.path.exists(file):
        return send_file(open(file, "rb"), mimetype=mime)
    else:
        return redirect(url, code=302)


@app.route('/api/core/refreshCache', methods=['GET'])
def refreshCache():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    if not api.isAdmin(request.args['token']):
        abort(403)
    api.refreshCache()
    return jsonify({'status': "ok"})

@app.route('/api/core/runPersonsScan', methods=['GET'])
def runPersonsScan():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    if not api.isAdmin(request.args['token']):
        abort(403)
    api.runPersonsScan()
    return jsonify({'status': "ok"})

@app.route('/sw_content.js')
def getServiceWorker():
    path = 'static/js/sw_content.js'
    mime = mimetypes.guess_type(path, strict=False)[0]
    return send_file(open(path, "rb"), mimetype=mime, as_attachment=True, attachment_filename=path[path.rfind('/')+1:])


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


@app.route('/api/player/start')
def tvs_startTranscoder():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    s = api.startPlayer(request.args['token'], request.args)
    if s:
        return jsonify({'response':'ok'})
    else:
        abort(403)

@app.route('/api/player/m3u8')
def getTranscoderM3U8():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    token = request.args['token']
    #add time to fileUrl prevent browser caching
    fileUrl = "/api/player/file?token="+token+"&time="+str(time.time())+"&name="
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

@app.route('/api/player/file')
def getTranscoderFile():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    name = request.args['name']
    token = request.args['token']
    #send transcoded file
    file = 'out/'+str(token)+'/'+name
    if os.path.exists(file):
        if '/' not in name and '/' not in token:
            return send_file(open(file, "rb"), mimetype='video/MP2T', as_attachment=True, attachment_filename=file[file.rfind('/')+1:])
        else:
            abort(403)
    else:
        abort(404)

@app.route('/api/player/getFile')
def player_getFile():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)

    path = api.getMediaPath(request.args['token'], request.args['mediaType'], request.args['mediaData'])
    if os.path.exists(path):
        return getFile(path, 'video')
    else:
        abort(404)

@app.route('/api/player/getInfos', methods=['GET'])
def player_getFileInfos():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.getFileInfos(request.args['token'], request.args['mediaType'], request.args['mediaData']))

@app.route('/api/player/stop', methods=['GET'])
def playbackEnd():
    t = request.args['token']
    if not api.checkToken(t):
        abort(401)
    #set as viewed for user, and stop transcoder if started
    s = api.setWatchTime(t, request.args['mediaType'], request.args['mediaData'], request.args.get('endTime'))
    api.stopPlayer(t)
    return jsonify({'response':s})

######################################################## TVS #############################################################################

@app.route('/api/tvs/getNextEpisodes', methods=['GET'])
def tvs_getNextEps():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.tvs_getNextEps())

@app.route('/api/tvs/getEpisodes', methods=['GET'])
def tvs_getEps():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.tvs_getEps(request.args['token'], request.args['idShow'], request.args.get('season')))

@app.route('/api/tvs/getSeasons', methods=['GET'])
def tvs_getSeasons():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.tvs_getSeasons(request.args['token'], request.args['idShow'], request.args.get('season')))

@app.route('/api/tvs/getShows', methods=['GET'])
def tvs_getShows():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.tvs_getShows(request.args['token'], False))

@app.route('/api/tvs/getShowsMultipleResults', methods=['GET'])
def tvs_getShowsMr():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.tvs_getShows(request.args['token'], True))

@app.route('/api/tvs/getShow', methods=['GET'])
def tvs_getShow():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.tvs_getShow(request.args['token'], request.args['idShow']))

@app.route('/api/tvs/getPersons', methods=['GET'])
def tvs_getPersons():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.getPersons(2, request.args['idShow']))

@app.route('/api/tvs/getTags', methods=['GET'])
def tvs_getTags():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.getTags(2, request.args['idShow']))

@app.route('/api/tvs/setID', methods=['GET'])
def tvs_setID():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    if api.isAdmin(request.args['token']):
        return jsonify(api.tvs_setID(request.args['idShow'], request.args['id']))
    else:
        abort(401)

@app.route('/api/tvs/toggleEpisodeStatus', methods=['GET'])
def tvs_toggleWatchedEpisode():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    #set episode as watched for user
    s = api.tvs_toggleWatchedEpisode(request.args['token'], request.args['idEpisode'])
    return jsonify({'response':s})

@app.route('/api/tvs/toggleSeasonStatus', methods=['GET'])
def tvs_toggleWatchedSeason():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    #set show as watched for user
    s = api.tvs_toggleWatchedSeason(request.args['token'], request.args['idShow'], request.args.get('season'))
    return jsonify({'response':s})

@app.route('/api/tvs/runScan', methods=['GET'])
def tvs_runScan():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    if not api.isAdmin(request.args['token']):
        abort(403)
    api.tvs_runScan()
    return jsonify({'status': "ok"})

######################################################## MOVIES #############################################################################

@app.route('/api/movies/getMovies', methods=['GET'])
def mov_getData():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.mov_getData(request.args['token'], False))

@app.route('/api/movies/getShowsMultipleResults', methods=['GET'])
def mov_getDataMr():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    return jsonify(api.mov_getData(request.args['token'], True))

@app.route('/api/movies/setID', methods=['GET'])
def mov_setID():
    if 'token' not in request.args or not api.checkToken(request.args['token']):
        abort(401)
    if api.isAdmin(request.args['token']):
        return jsonify(api.mov_setID(request.args['idMovie'], request.args['id']))
    else:
        abort(401)