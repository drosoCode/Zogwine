import flask
from flask import request, jsonify, abort, send_file, Response, stream_with_context, render_template, redirect
from flask_cors import CORS
import requests
import mimetypes
import os
import re
from base64 import b64decode
import time
import json
import base64
import hashlib
import secrets

from dbHelper import sql
from indexer import scanner
from log import logger, getLogs
from transcoder import transcoder

"""
DB:
    mediaType: 1=tv_show ep
               2=tv_show
               3=movie
               
"""

with open('config/config_dev.json') as f:
    data = json.load(f)
    configData = data
    sqlConnection = sql(host=data["db"]["host"],user=data["db"]["user"],password=data["db"]["password"],database=data["db"]["name"], use_unicode=True, charset='utf8')
    userFiles = {}
    userTokens = {}
    logger.info('Server Class Instancied Successfully')

app = flask.Flask(__name__, static_url_path='')
CORS(app)

app.config["DEBUG"] = True

@app.before_request
def before_request():
    if request.endpoint not in ['authenticateUser', 'getImage'] and ('token' not in request.args or not request.args['token'] in userTokens):
        abort(401)

def checkArgs(args):
    for a in args:
        if a not in request.args:
            abort(404)
            return False
    return True

def checkUser(prop):
    if prop == 'admin':
        d = getUserData(request.args['token'])
        if "admin" in d and d["admin"]:
            return True
        else:
            abort(403)

def generateToken(userID):
    t = secrets.token_hex(20)
    userTokens[t] = userID
    return t

def removeToken(token):
    uid = userTokens[token]
    del userTokens[token]
    if sum(u == uid for u in userTokens.values()) == 0:
        if uid in userFiles:
            userFiles[uid].stop()
            del userFiles[uid]

def addCache(data):
    file = 'out/cache/'+data
    if not os.path.exists(file):
        with open(file, 'wb') as f:
            logger.debug('Adding '+file+' to cache')
            f.write(requests.get(b64decode(data).decode()).content)

@app.route('/', methods=['GET'])
def home():
    return redirect('index.html', code=302)

#region main

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
def getStatistics():
    avgEpTime = 0.5 #h
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(idStatus) AS watchedEpCount, SUM(watchCount) AS watchedEpSum FROM status WHERE watchCount > 0 AND mediaType = 1 AND idUser = %(idUser)s;", {'idUser': userTokens[request.args['token']]})
    dat1 = cursor.fetchone()
    cursor.execute("SELECT COUNT(DISTINCT idShow) AS tvsCount, COUNT(idEpisode) AS epCount FROM episodes;")
    dat2 = cursor.fetchone()
    if "watchedEpSum" not in dat1 or dat1["watchedEpSum"] == None:
        dat1["watchedEpSum"] = 0
    return {"watchedEpCount":int(dat1["watchedEpCount"]), "watchedEpSum":int(dat1["watchedEpSum"]), "tvsCount":int(dat2["tvsCount"]), "epCount": int(dat2["epCount"]), "lostTime": avgEpTime * int(dat1["watchedEpSum"])}

@app.route('/api/core/getLogs')
def getServerLogs():
    checkUser('admin')
    try:
        l = int(request.args['amount'])
    except Exception:
        l = 20
    return jsonify(getLogs(l))

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
    checkUser('admin')
    tvs_refreshCache()
    mov_refreshCache()

    cursor = sqlConnection.cursor(dictionary=True)
    #refresh tags cache
    cursor.execute("SELECT icon FROM tags;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None:
            addCache(d["icon"])
    #refresh persons cache
    cursor.execute("SELECT icon FROM persons;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None:
            addCache(d["icon"])
    return jsonify({'response': 'ok'})

@app.route('/api/core/runPersonsScan', methods=['GET'])
def runPersonsScan():
    checkUser('admin')
    scanner(sqlConnection, 'persons', configData["api"]).getObject().scan()
    return jsonify({'response': 'ok'})

@app.route('/api/users/authenticate', methods=['GET','POST'])
def authenticateUser():
    checkArgs(['user', 'password'])
    user = request.args['user']
    password = hashlib.sha256(bytes(request.args['password'], 'utf-8')).hexdigest()
    cursor = sqlConnection.cursor(dictionary=True)
    if user != "" and password != "":
        r = "SELECT idUser FROM users WHERE user = '"+str(user)+"' AND password = '"+str(password)+"';"
        cursor.execute(r)
        dat = cursor.fetchone()
        if dat != None and "idUser" in dat:
            logger.info('User: '+str(user)+' successfully authenticated')
            return jsonify({'response': generateToken(dat["idUser"])})
        else:
            logger.warning('Bad Authentication for user: '+str(user))
            return jsonify({'response': 'error'})
    else:
        logger.warning('Empty User or Password for authentication')
        return jsonify({'response': 'error'})

def getUserData(token):
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT name, icon, admin, kodiLinkBase FROM users WHERE idUser = %(idUser)s", {'idUser': userTokens[token]})
    return cursor.fetchone()

@app.route('/api/users/data', methods=['GET','POST'])
def getUserDataFlask():
    return jsonify(getUserData(request.args['token']))

@app.route('/api/core/getPersons', methods=['GET'])
def getPersons():
    checkArgs(['mediaType', 'mediaData'])
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT p.idPers, role, name, gender, birthdate, deathdate, description, known_for, CONCAT('/cache/image?id=',icon) AS icon " \
                    "FROM persons p, persons_link l " \
                    "WHERE p.idPers = l.idPers" \
                    " AND mediaType = %(mediaType)s AND idMedia = %(mediaData)s;", {'mediaType': request.args['mediaType'], 'mediaData': request.args['mediaData']})
    return jsonify(cursor.fetchall())

@app.route('/api/core/getTags', methods=['GET'])
def getTags():
    checkArgs(['mediaType', 'mediaData'])
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT t.idTag, name, value, CONCAT('/cache/image?id=',icon) AS icon " \
                    "FROM tags t, tags_link l " \
                    "WHERE t.idTag = l.idTag" \
                    " AND mediaType = %(mediaType)s AND idMedia = %(mediaData)s;", {'mediaType': request.args['mediaType'], 'mediaData': request.args['mediaData']})
    return jsonify(cursor.fetchall())

#endregion

#region player

@app.route('/api/player/start')
def startPlayer():
    uid = userTokens[request.args['token']]
    logger.info('Starting transcoder for user '+str(uid))

    userFiles[uid].enableHLS(True, configData["config"]['hlsTime'])
    if 'audioStream' in request.args:
        userFiles[uid].setAudioStream(request.args.get('audioStream'))
    if 'subStream' in request.args:
        userFiles[uid].setSub(request.args.get('subStream'))
    if 'startFrom' in request.args:
        userFiles[uid].setStartTime(request.args.get('startFrom'))
    if 'resize' in request.args:
        userFiles[uid].resize(request.args.get('resize'))

    userFiles[uid].start()
    return jsonify({'response':'ok'})

@app.route('/api/player/m3u8')
def getTranscoderM3U8():
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

def getMediaPath(token, mediaType, mediaData):
    if mediaType == '1':
        #tvs episode
        return tvs_getEpPath(mediaData)
    elif mediaType == '3':
        #movie
        pass
    else:
        return None

@app.route('/api/player/getFile')
def player_getFile():
    checkArgs(['mediaType', 'mediaData'])
    path = getMediaPath(request.args['token'], request.args['mediaType'], request.args['mediaData'])
    if os.path.exists(path):
        return getFile(path, 'video')
    else:
        abort(404)

def getFileInfos(token, mediaType, mediaData):
    uid = userTokens[token]
    path = getMediaPath(token, mediaType, mediaData)
    tr = transcoder(path, configData['config']['outDir']+'/'+token, configData['config']['encoder'], configData['config']['crf'])

    #get last view end if available
    st = None
    if mediaType == 1:
        cursor = sqlConnection.cursor(dictionary=True)
        cursor.execute("SELECT viewTime FROM tvs_status WHERE idUser = %(idUser)s AND idEpisode = %(idEpisode)s;", {'idUser': userTokens[token], 'idEpisode': mediaData})
        data = cursor.fetchone()
        if data != None and "viewTime" in data:
            st = float(data["viewTime"])
    
    if st is not None:
        tr.setStartTime(st)

    userFiles[uid] = tr
    return tr.getFileInfos()

@app.route('/api/player/getInfos', methods=['GET'])
def player_getFileInfos():
    checkArgs(['mediaType', 'mediaData'])
    return jsonify(getFileInfos(request.args['token'], request.args['mediaType'], request.args['mediaData']))

@app.route('/api/player/stop', methods=['GET'])
def player_stop():
    token = request.args['token']
    mediaType = request.args['mediaType']
    mediaData = request.args['mediaData']
    endTime = request.args.get('endTime')
    #set watch time
    if mediaType == '1':
        tvs_setWatchTime(token, mediaData, endTime)
    #stop transcoder
    logger.info('Stopping transcoder for user '+str(userTokens[token]))
    userFiles[userTokens[token]].stop()
    del userFiles[userTokens[token]]
    
    return jsonify({'response':'ok'})

#endregion

#region tvs

def tvs_getEpPath(idEpisode):
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT CONCAT(t.path, '/', e.path) AS path FROM tv_shows t INNER JOIN episodes e ON t.idShow = e.idShow WHERE e.idEpisode = %(idEpisode)s;", {'idEpisode': idEpisode})
    path = configData["config"]["tvsDirectory"]+'/'+cursor.fetchone()['path']
    logger.debug('Getting episode path for id:'+str(idEpisode)+' -> '+path)
    return path

def tvs_refreshCache():
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT icon, fanart FROM tv_shows;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None:
            addCache(d["icon"])
        if d["fanart"] != None:
            addCache(d["fanart"])
    cursor.execute("SELECT icon FROM episodes;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None:
            addCache(d["icon"])
    cursor.execute("SELECT icon FROM seasons;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None:
            addCache(d["icon"])
    cursor.execute("SELECT icon FROM upcoming_episodes;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None:
            addCache(d["icon"])

def tvs_setWatchTime(token, idEpisode, endTime=None):
    uid = userTokens[token]
    if endTime is not None:
        endTime = userFiles[uid].getWatchedDuration(endTime)
        duration = float(userFiles[uid].getFileInfos()['general']['duration'])

        cursor = sqlConnection.cursor(dictionary=True)
        cursor.execute("SELECT idStatus, watchCount FROM status WHERE idUser = %(idUser)s AND mediaType = 1 AND idMedia = %(idEpisode)s;", {'idUser': uid, 'idEpisode': idEpisode})
        data = cursor.fetchone()
        viewAdd = 0
    
        if endTime > duration * configData['config']['watchedThreshold']:
            viewAdd = 1

        if data != None and "watchCount" in data:
            cursor.execute("UPDATE status SET watchCount = %(watchCount)s, watchTime = %(watchTime)s WHERE idStatus = %(idStatus)s;", {'watchCount':str(data["watchCount"]+viewAdd), 'watchTime': str(endTime), 'idStatus': str(data["idStatus"])})
        else:
            cursor.execute("INSERT INTO tvs_status (idUser, idEpisode, watchCount, watchTime) VALUES (%s, %s, 1, %s);", (str(uid), str(idEpisode), str(viewAdd), str(endTime)))

        return True
    else:
        return False

@app.route('/api/tvs/getUpcomingEpisodes', methods=['GET'])
def tvs_getUpcomingEpisodes():
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT u.idEpisode AS id, u.title AS title, t.title AS showTitle, u.overview AS overview, CONCAT('/cache/image?id=',COALESCE(u.icon, t.fanart)) AS icon," \
                    "u.season AS season, u.episode AS episode, u.date AS date, u.idShow AS idShow "\
                    "FROM upcoming_episodes u, tv_shows t "\
                    "WHERE u.idShow = t.idShow AND u.date >= DATE(SYSDATE())" \
                    "ORDER BY date;")
    return jsonify(cursor.fetchall())

@app.route('/api/tvs/runUpcomingScan', methods=['GET'])
def tvs_runUpcomingScan():
    scanner(sqlConnection, 'tvs', configData["api"]).getObject().scanUpcomingEpisodes()
    return jsonify({'status': "ok"})

def tvs_getEps(token, idShow, season=None):
    idUser = userTokens[token]
    cursor = sqlConnection.cursor(dictionary=True)
    s = ''
    dat = {'idUser': idUser, 'idShow': idShow}
    if season is not None:
        dat['season'] = season
        s = "AND season = %(season)s "
    cursor.execute("SELECT idEpisode AS id, title, overview, CONCAT('/cache/image?id=',icon) AS icon," \
                    "season, episode, rating, scraperName, scraperID, "\
                    "(SELECT watchCount FROM status WHERE idMedia = e.idEpisode AND mediaType = 1 AND idUser = %(idUser)s) AS watchCount " \
                    "FROM episodes e "\
                    "WHERE idShow = %(idShow)s " + s + "" \
                    "ORDER BY season, episode;", dat)
    return cursor.fetchall()

@app.route('/api/tvs/getEpisodes', methods=['GET'])
def tvs_getEpsFlask():
    checkArgs(['idShow'])
    return jsonify(tvs_getEps(request.args['token'], request.args['idShow'], request.args.get('season')))

@app.route('/api/tvs/getSeasons', methods=['GET'])
def tvs_getSeasons():
    checkArgs(['idShow'])
    idUser = userTokens[request.args['token']]
    cursor = sqlConnection.cursor(dictionary=True)
    season = request.args.get('season')
    s = ''
    dat = {'idUser': idUser, 'idShow': request.args['idShow']}
    if season is not None:
        dat['season'] = season
        s = "AND season = %(season)s "
    cursor.execute("SELECT title, overview, CONCAT('/cache/image?id=',icon) AS icon," \
                    "season, premiered, "\
                    "(SELECT COUNT(*) FROM episodes WHERE idShow = s.idShow AND season = s.season) AS episodes, "
                    "(SELECT COUNT(watchCount) FROM status WHERE idMedia IN (SELECT idEpisode FROM episodes WHERE idShow = s.idShow AND season = s.season) AND mediaType = 1 AND idUser = %(idUser)s) AS watchedEpisodes " \
                    "FROM seasons s " \
                    "WHERE idShow = %(idShow)s " + s + ""\
                    "ORDER BY season;", dat)
    return jsonify(cursor.fetchall())

def tvs_getShows(token, mr=False):
    idUser = userTokens[token]
    cursor = sqlConnection.cursor(dictionary=True)
    mrDat = ''
    if mr:
        mrDat = 'NOT '
    query = "SELECT idShow AS id, title,"\
                "CONCAT('/cache/image?id=',icon) AS icon,"\
                "rating, premiered, genre, multipleResults,"\
                "(SELECT MAX(season) FROM episodes WHERE idShow = t.idShow) AS seasons,"\
                "(SELECT COUNT(idEpisode) FROM episodes WHERE idShow = t.idShow) AS episodes,"\
                "(SELECT COUNT(*) FROM episodes e LEFT JOIN status s ON (s.idMedia = e.idEpisode) "\
                    "WHERE e.idEpisode = s.idMedia AND s.mediaType = 1 AND watchCount > 0  AND idUser = %(idUser)s AND idShow = t.idShow) AS watchedEpisodes "\
                "FROM tv_shows t "\
                "WHERE multipleResults IS " + mrDat + "NULL ORDER BY title;"
    cursor.execute(query, {'idUser': str(idUser)})
    return cursor.fetchall()

@app.route('/api/tvs/getShows', methods=['GET'])
def tvs_getShowsFlask():
    return jsonify(tvs_getShows(request.args['token'], False))

@app.route('/api/tvs/getShowsMultipleResults', methods=['GET'])
def tvs_getShowsMr():
    return jsonify(tvs_getShows(request.args['token'], True))

@app.route('/api/tvs/getShow', methods=['GET'])
def tvs_getShow():
    checkArgs(['idShow'])
    idUser = userTokens[request.args['token']]
    cursor = sqlConnection.cursor(dictionary=True)
    query = "SELECT idShow AS id," \
                "title, overview, " \
                "CONCAT('/cache/image?id=',icon) AS icon, " \
                "CONCAT('/cache/image?id=',fanart) AS fanart, " \
                "rating, premiered, genre, scraperName, scraperID, path," \
                "(SELECT MAX(season) FROM episodes WHERE idShow = t.idShow) AS seasons," \
                "(SELECT COUNT(idEpisode) FROM episodes WHERE idShow = t.idShow) AS episodes," \
                "(SELECT COUNT(*) FROM episodes e LEFT JOIN status s ON (s.idMedia = e.idEpisode)" \
                    "WHERE e.idEpisode = s.idMedia AND s.mediaType = 1 AND watchCount > 0  AND idUser = %(idUser)s and idShow = t.idShow) AS watchedEpisodes," \
                "CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 'tv_shows'),scraperID) AS scraperLink " \
                "FROM tv_shows t " \
                "WHERE multipleResults IS NULL AND idShow = %(idShow)s ORDER BY title;"
    cursor.execute(query, {'idUser': str(idUser), 'idShow': str(request.args['idShow'])})
    return jsonify(cursor.fetchone())

@app.route('/api/tvs/setID', methods=['GET'])
def tvs_setID():
    checkArgs(['idShow', 'id'])
    checkUser('admin')

    idShow = request.args['idShow']
    resultID = request.args['id']
    #the resultID is the one from the json list of multipleResults entry
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT multipleResults FROM tv_shows WHERE idShow = %(idShow)s;", {'idShow': str(idShow)})
    data = json.loads(cursor.fetchone()["multipleResults"])[int(resultID)]
    cursor.execute("UPDATE tv_shows SET scraperName = %(scraperName)s, scraperID = %(scraperId)s, scraperData = %(scraperData)s, forceUpdate = 1, multipleResults = NULL WHERE idShow = %(idShow)s;", {'scraperName': data["scraperName"], 'scraperId': data["id"], 'scraperData': data["scraperData"], 'idShow': idShow})
    sqlConnection.commit()
    return jsonify({'status': "ok"})

def tvs_toggleWatchedEpisode(token, idEpisode, watched=None):
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT watchCount FROM status WHERE idUser = %(idUser)s AND mediaType = 1 AND idMedia = %(idEpisode)s;", {'idEpisode': str(idEpisode), 'idUser': str(userTokens[token])})
    data = cursor.fetchone()
    count = 0
    if data != None and "watchCount" in data:
        #update
        count = data["watchCount"]
        if watched is False or count > 0:
            count = 0
        else:
            count = 1
        cursor.execute("UPDATE status SET watchCount = %(watchCount)s WHERE idUser = %(idUser)s AND mediaType = 1 AND idMedia = %(idMedia)s;", {'watchCount': str(count), 'idUser': str(userTokens[token]), 'idMedia': str(idEpisode)})
    elif watched is not False:
        cursor.execute("INSERT INTO status (idUser, mediaType, idMedia, watchCount) VALUES (%(idUser)s, 1, %(idMedia)s, 1);", {'idUser': str(userTokens[token]), 'idMedia': str(idEpisode)})
    sqlConnection.commit()
    return True

@app.route('/api/tvs/toggleEpisodeStatus', methods=['GET'])
def tvs_toggleWatchedEpisodeFlask():
    checkArgs(['idEpisode'])
    #set episode as watched for user
    tvs_toggleWatchedEpisode(request.args['token'], request.args['idEpisode'])
    return jsonify({'response':'ok'})

@app.route('/api/tvs/toggleSeasonStatus', methods=['GET'])
def tvs_toggleWatchedSeason():
    checkArgs(['idShow'])
    cursor = sqlConnection.cursor(dictionary=True)
    dat = {'idUser': userTokens[token], 'idShow': idShow}
    watched = True

    season = request.args.get('season')
    if season is not None:
        dat['season'] = season
        s = "AND season = %(season)s"
    cursor.execute("SELECT SUM(watchCount) AS watched FROM status WHERE idUser = %(idUser)s AND mediaType = 1 " \
        "AND idMedia IN (SELECT idEpisode FROM episodes WHERE idShow = %(idShow)s " + s + ");", dat)
    isWatched = cursor.fetchone()['watched']
    if isWatched is not None and int(isWatched) > 0:
        watched = False

    ids = tvs_getEps(token, idShow)
    for i in ids:
        if season is None or int(season) == int(i["season"]):
            tvs_toggleWatchedEpisode(token, i["id"], watched)
   
    return jsonify({'response':'ok'})

@app.route('/api/tvs/runScan', methods=['GET'])
def tvs_runScan():
    checkUser('admin')
    scanner(sqlConnection, 'tvs', configData["api"]).scanDir(configData["config"]["tvsDirectory"])
    return jsonify({'response': "ok"})

#endregion

#region movies

@app.route('/api/movies/runScan', methods=['GET'])
def mov_runScan():
    checkUser('admin')
    scanner(sqlConnection, 'movies', configData["api"]).scanDir(configData["config"]["moviesDirectory"])
    return jsonify({'response': 'ok'})

def mov_getData(token, mr=False):
    idUser = userTokens[token]
    cursor = sqlConnection.cursor(dictionary=True)
    mrDat = ''
    if mr:
        mrDat = 'NOT '
    cursor.execute("SELECT idMovie AS id, title, overview, CONCAT('/cache/image?id=',icon) AS icon, CONCAT('/cache/image?id=',fanart) AS fanart, rating, premiered, genre, scraperName, scraperID, path, multipleResults, (SELECT COUNT(st.idStatus) FROM movies mov LEFT JOIN status st ON (st.idMedia = mov.idMovie) WHERE idUser = %(idUser)s AND st.mediaType = 3) AS viewCount, CONCAT((SELECT scraperURL FROM scrapers WHERE scraperName = t.scraperName AND mediaType = 'movies'),scraperID) AS scraperLink FROM movies t WHERE multipleResults IS " + mrDat + "NULL ORDER BY title;", {'idUser': idUser})
    return cursor.fetchall()

@app.route('/api/movies/getMovies', methods=['GET'])
def mov_getDataFlask():
    return jsonify(mov_getData(request.args['token']))

@app.route('/api/movies/getShowsMultipleResults', methods=['GET'])
def mov_getDataMr():
    return jsonify(mov_getData(request.args['token'], True))

@app.route('/api/movies/setID', methods=['GET'])
def mov_setID():
    checkUser('admin')
    checkArgs(['idMovie', 'id'])
    idMovie = reques.args['idMovie']
    resultID = reques.args['id']
    #the resultID is the one from the json list of multipleResults entry
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT multipleResults FROM movies WHERE idMovie = "+str(idMovie)+";")
    data = json.loads(cursor.fetchone()["multipleResults"])[int(resultID)]
    cursor.execute("UPDATE movies SET scraperName = %(scraperName)s, scraperID = %(scraperID)s, scraperData = %(scraperData)s, forceUpdate = 1, multipleResults = NULL WHERE idMovie = %(idMovie)s;", {'scraperName': data["scraperName"], 'scraperID': data["id"], 'scraperData': data["scraperData"], 'idMovie': idMovie})
    sqlConnection.commit()
    return jsonify({'result': 'ok'})

def mov_refreshCache():
    cursor = sqlConnection.cursor(dictionary=True)
    cursor.execute("SELECT icon, fanart FROM movies;")
    data = cursor.fetchall()
    for d in data:
        if d["icon"] != None:
            addCache(d["icon"])
        if d["fanart"] != None:
            addCache(d["fanart"])

#endregion