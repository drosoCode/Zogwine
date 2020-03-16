
document.addEventListener('DOMContentLoaded', () => {

    window.addEventListener('hashchange', () => changePage());
    window.addEventListener("beforeunload",() => checkPlaybackEnd());
    document.querySelector("#logout").addEventListener('click', () => logout());
    document.querySelector("#userNavSettings").addEventListener('click', () => showSettings());
    document.querySelector("#userNavPlayerReload").addEventListener('click', () => updatePlay(5));
    changePage();
    
});

function httpGet(url, async=false)
{    
    if(url.indexOf("?") >= 0)
        url += "&time="+new Date().getTime()
    else
        url += "?time="+new Date().getTime()
        
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", url, async); // false for synchronous request
    xmlHttp.send( null );

    if(xmlHttp.status == 403 || xmlHttp.status == 401)
        logout(true);
    else if(xmlHttp.status >= 500)
        notify("Internal Server Error","error");
        
    return xmlHttp.responseText;
}

//var apiEndpoint = "http://192.168.1.9:8080/api/";
var apiEndpoint = "api/";
var tvshows;
var tvsE;
var fileInfos;
var userToken = null;
var playing = false;

function changePage(clear=false) 
{
    document.querySelector("#userNavPlayerNext").innerHTML = "";
    document.querySelector("#userNavPlayerReload").hidden = true;

    let hash = location.hash.slice(1);

    checkPlaybackEnd();
    playing = false;
    
    if(userToken == null)
    {
        document.querySelector("#homeNav").classList.remove("active");
        document.querySelector("#tvshowsNav").classList.remove("active");
        document.querySelector("#home").hidden = true;
        document.querySelector("#content").hidden = true;
        document.querySelector("#login").hidden = false;
        document.querySelector("#userNav").hidden = true;
    }
    else if(clear)
    {
        document.querySelector("#homeNav").classList.remove("active");
        document.querySelector("#tvshowsNav").classList.remove("active");
        document.querySelector("#home").hidden = true;
        document.querySelector("#content").hidden = true;
        document.querySelector("#login").hidden = true;
        document.querySelector("#content").innerHTML = "";
    }
    else if(hash == "tvshows")
    {
        document.querySelector("#homeNav").classList.remove("active");
        document.querySelector("#tvshowsNav").classList.add("active");
        document.querySelector("#home").hidden = true;
        document.querySelector("#content").hidden = false;
        document.querySelector("#login").hidden = true;
        showTVS();
    }
    else if(hash.indexOf("tvshow_") != -1)
    {
        document.querySelector("#homeNav").classList.remove("active");
        document.querySelector("#tvshowsNav").classList.add("active");
        document.querySelector("#home").hidden = true;
        document.querySelector("#content").hidden = false;
        document.querySelector("#login").hidden = true;
        showTVSEpisodes(hash.substring(7));
    }
    else
    {
        document.querySelector("#homeNav").classList.add("active");
        document.querySelector("#tvshowsNav").classList.remove("active");
        document.querySelector("#content").hidden = true;
        document.querySelector("#home").hidden = false;
        document.querySelector("#login").hidden = true;
        showHome();
    }
}

function notify(text, type='error')
{
    new Noty({
        type: type,
        text: text,
        theme: 'bootstrap-v4',
        timeout: 2000,
        layout: 'topCenter'
    }).show();
}

function logout(fail=false)
{
    userToken = null;
    document.querySelector("#login_user").value = '';
    document.querySelector("#login_password").value = '';
    if(fail)
        notify("Forbidden Action","error");
    else
        notify("Signed Out","success");
    changePage();
}

function login()
{
    let user = document.querySelector("#login_user").value;
    let pass = document.querySelector("#login_password").value;
    let ret = httpGet(apiEndpoint+"users/authenticate?user="+user+"&password="+pass);
    try
    {
        userToken = JSON.parse(ret)["response"];
        let userData = JSON.parse(httpGet(apiEndpoint+"users/data?token="+userToken));
        document.querySelector("#userNavName").textContent = userData['name'];
        if(userData['admin'])
            document.querySelector("#userNavSettings").hidden = false;
        else
            document.querySelector("#userNavSettings").hidden = true;
        document.querySelector("#userNav").hidden = false;
        changePage();
    }
    catch (e)
    {
        notify("Authentification Failed","error");
    }
}

function showHome()
{
    let userData = JSON.parse(httpGet(apiEndpoint+"users/data?token="+userToken));
    let stats = JSON.parse(httpGet(apiEndpoint+"tvs/getStatistics?token="+userToken));
    document.querySelector("#statsWatchedEP").textContent = stats["watchedEpCount"];
    document.querySelector("#statsLostTime").textContent = stats["lostTime"]+"H";
    document.querySelector("#statsAvTVS").textContent = stats["tvsCount"];
    document.querySelector("#statsAvEP").textContent = stats["epCount"];
    document.querySelector("#cardUserName").textContent = userData["name"];
    document.querySelector("#cardUserImg").setAttribute("src","../static/icons/"+userData["icon"]);
}

function showTVS()
{
    tvshows = JSON.parse(httpGet(apiEndpoint+"tvs/getShows?token="+userToken));
    
    let i = 0;
    let cards = "";
    while(i<tvshows.length)
    {
        if(tvshows[i]["title"] != null)
            cards += makeTVSCard(i);
        i++;
    }
    document.querySelector("#content").innerHTML = "<div class=\"row\">"+cards+"</div>";
}

function makeTVSCard(id)
{
    let data = tvshows[id]
    let descData = "<div class=\"btn-group btn-sm\" role=\"group\">"
    descData += "<a type=\"button\" class=\"btn btn-primary btn-sm\" href=\"#tvshow_"+data["id"]+"\">Play</a>"
    descData += "<button type=\"button\" class=\"btn btn-info btn-sm\" onclick=\"showTVSInfo("+id+")\">Info</button>"
    if(data["viewedEpisodes"] == data["episodes"])
    {
        descData += "<button type=\"button\" class=\"btn btn-success disabled btn-sm\">Viewed <span class=\"badge badge-light\">"+data["episodes"]+"</span></btn>";
    }
    else if(data["viewedEpisodes"] > 0)
    {
        descData += "<button type=\"button\" class=\"btn btn-warning disabled btn-sm\">Viewed <span class=\"badge badge-light\">"+data["viewedEpisodes"]+"/"+data["episodes"]+"</span></btn>";
    }
    else
    {
        descData += "<button type=\"button\" class=\"btn btn-danger disabled btn-sm\">Not Viewed <span class=\"badge badge-light\">"+data["episodes"]+"</span></btn>";
    }
    descData += "</div>"

    let card = "<div class=\"col-xl-3 col-lg-6 col-md-6 col-sm-12 col-xs-12\">"
    card += "<div class=\"card text-white bg-dark\">"
        card += "<div class=\"row no-gutters\">"
                card += "<img src=\""+data["icon"]+"\" height=\"200px\" class=\"card-img col-4\">"
                card += "<div class=\"card-body  col-8 pl-3\">"
                    card += "<h5 class=\"card-title\">"+data["title"]+"</h5>"
                    card += "<p class=\"card-text\"><small class=\"text-muted\">Premiered: "+data["premiered"]+" | Rating: "+data["rating"]+"</small></p>"  
                    card += descData
                card += "</div>"
        card += "</div>"
    card += "</div>"
    card += "</div>"
    return card
}

function showTVSInfo(id)
{
    let data = tvshows[id];
    let infos = "Genre: "+JSON.parse(data["genre"]).join(" / ")+"<br/>"
    infos += "Premiered: "+data["premiered"]+"<br/>"
    infos += "Rating: "+data["rating"]+"<br/>"
    infos += "Seasons: "+data["seasons"]+"<br/>"
    infos += "Episodes: "+data["episodes"]+"<br/>"
    infos += "Viewed Episodes: "+data["viewedEpisodes"]+"<br/>"
    let scraperName = data["scraperLink"].match("(?:\\/\\/)([^\\/]*)(?=\\/)")[1]
    infos += "More Infos: <a target=\"_blank\" rel=\"noopener noreferrer\" href="+data["scraperLink"]+">"+scraperName+"</a><br/>"
    infos += "Description: <br/>"+data["overview"]
    document.getElementById("infoModalTitle").innerText = data["title"];
    document.getElementById("infoModalContent").innerHTML = infos;
    document.getElementById("cssContainer").innerHTML = ".modal-backdrop { background-image: url(\""+data["fanart"]+"\");background-size: cover;background-position: center center; background-repeat: no-repeat; background-attachment: fixed; position: fixed;}";
    $('#infoModal').modal('show');
}

function showTVSEpisodes(id)
{
    tvsE = JSON.parse(httpGet(apiEndpoint+"tvs/getEpisodes?idShow="+id+"&token="+userToken));
    let cards = "";
    let season = -1;
    let i = 0;
    while(i<tvsE.length)
    {
        if(tvsE[i]["season"] != season)
        {
            if(season != -1)
                cards += "</div>"

            cards += "<div class=\"alert alert-dark mt-4\" role=\"alert\">"
                cards += "Season "+tvsE[i]["season"]
                cards += "<button type=\"button\" class=\"btn btn-sm btn-outline-info mx-4\" onclick=seasonOptions(0,"+id+","+tvsE[i]["season"]+")><i class=\"fas fa-check-circle\"></i>&nbsp;Toggle Status</button>"
                cards += "<button type=\"button\" class=\"btn btn-sm btn-outline-warning mx-4\" onclick=seasonOptions(1,"+id+","+tvsE[i]["season"]+")><i class=\"fas fa-download\"></i>&nbsp;Download</button>"
            cards += "</div>"
            cards += "<div class=\"row\">"

            season = tvsE[i]["season"];
        }
        cards += makeTVSEpisodesCard(i);
        i++;
    }
    document.getElementById("content").innerHTML = cards;
}

function seasonOptions(type, id, season)
{
    if(type == 0)
    {
        //set season as watched/unwatched
        httpGet(apiEndpoint+"tvs/toggleViewedTVS?idShow="+id+"&season="+season+"&token="+userToken);
        notify("Season status updated","success");
    }
    else if(type == 1)
    {
        //download a season
        let data = JSON.parse(httpGet(apiEndpoint+"tvs/getEpisodes?idShow="+id+"&token="+userToken));
        for(ep of data)
        {
            if(ep["season"] == season)
            {
                let link = apiEndpoint+"tvs/getFile?idEpisode="+ep["id"]+"&token="+userToken;
                let win = window.open(link, '_blank');
                win.focus();
            }
        }
    }
}

function makeTVSEpisodesCard(id)
{
    let data = tvsE[id];
    let descData = "<div class=\"btn-group btn-sm\" role=\"group\">"
    descData += "<button type=\"button\" class=\"btn btn-primary btn-sm\" onclick=\"showPlay('"+id+"')\">Play</button>"
    descData += "<button type=\"button\" class=\"btn btn-info btn-sm\" onclick=\"showTVSEpisodeInfo('"+id+"')\">Info</button>"
    if(data["viewCount"] > 0)
    {
        descData += "<button type=\"button\" class=\"btn btn-success disabled btn-sm\">Viewed <span class=\"badge badge-light\">"+data["viewCount"]+"</span></btn>";
    }
    else
    {
        descData += "<button type=\"button\" class=\"btn btn-danger disabled btn-sm\">Not Viewed</btn>";
    }
    descData += "</div>"

    let card = "<div class=\"col-xl-3 col-lg-4 col-md-6 col-sm-6 col-xs-12\">"
    card += "<div class=\"card text-white bg-dark\">"
        card += "<div class=\"row no-gutters\">"
                card += "<img src=\""+data["icon"]+"\" class=\"card-img-top\" height=\"200px\" width=\"30px\">"
                card += "<div class=\"card-body\">"
                    card += "<h5 class=\"card-title\">"+data["title"]+"</h5>"
                    card += "<p class=\"card-text\">Season "+data["season"]+" | Episode "+data["episode"]+"</p>"
                    card += "<p class=\"card-text\"><small class=\"text-muted\">Premiered: "+data["premiered"]+" | Rating: "+data["rating"]+"</small></p>"  
                    card += descData
                card += "</div>"
            card += "</div>"
    card += "</div>"
    card += "</div>"
    return card
}

function showTVSEpisodeInfo(id)
{
    let data = tvsE[id];
    let infos = "Season: "+data["season"]+"<br/>"
    infos += "Episode: "+data["episode"]+"<br/>"
    infos += "Premiered: "+data["premiered"]+"<br/>"
    infos += "Rating: "+data["rating"]+"<br/>"
    infos += "Description: <br/>"+data["overview"]
    document.getElementById("infoModalTitle").innerText = data["title"];
    document.getElementById("infoModalContent").innerHTML = infos;
    document.getElementById("cssContainer").innerHTML = "";
    $('#infoModal').modal('show');
}

function showPlay(id)
{
    checkPlaybackEnd();
    let data = tvsE[id];
    fileInfos = JSON.parse(httpGet(apiEndpoint+"tvs/fileInfos?idEpisode="+data["id"]+"&token="+userToken));

    let infos = "<button type=\"button\" class=\"btn btn-primary\"><i class=\"fas fa-burn\"></i>&nbsp;Video Codec&nbsp;<span class=\"badge badge-light\">"+fileInfos['general']['video_codec']+"</span></button>";
    infos += "&nbsp;<button type=\"button\" class=\"btn btn-primary\"><i class=\"fas fa-barcode\"></i>&nbsp;Video Format&nbsp;<span class=\"badge badge-light\">"+fileInfos['general']['format']+"</span></button>";
    infos += "&nbsp;<button type=\"button\" class=\"btn btn-primary\"><i class=\"fas fa-clock\"></i>&nbsp;Duration&nbsp;<span class=\"badge badge-light\">"+Math.round(fileInfos['general']['duration']/60)+" mins</span></button>";

    if(fileInfos['general']['extension'] != 'mp4')
    {
        infos += "<br><br><div class=\"form-row\">";
            infos += "<div class=\"col\"><label for=\"audioSelect\">Audio</label><select class=\"form-control\" id=\"audioSelect\">";
            for(let i in fileInfos['audio'])
            {
                infos += "<option value="+i+">"+fileInfos['audio'][i]["language"]+"</option>";
            }
            infos += "</select></div>"

            infos += "<div class=\"col\"><label for=\"subtitlesSelect\">Subtitles</label><select class=\"form-control\" id=\"subtitlesSelect\">";
            for(let i in fileInfos['subtitles'])
            {
                infos += "<option value="+i+">"+fileInfos['subtitles'][i]["language"]+" | "+fileInfos['subtitles'][i]["title"]+"</option>";
            }
            infos += "</select></div>"

        infos += "</div>";
        infos += "<br><br><button type=\"button\" class=\"btn btn-outline-success btn-block\" onclick=updatePlay(3,"+id+")><i class=\"fas fa-play-circle\"></i>&nbsp;Play</button>";
    }
    else
    {
        infos += "<br><br><button type=\"button\" class=\"btn btn-outline-success btn-block\" onclick=updatePlay(4,"+id+")><i class=\"fas fa-play-circle\"></i>&nbsp;Play</button>";
    }
    infos += "<br><div class=\"btn-group btn-block\" role=\"group\"><button type=\"button\" class=\"btn btn-warning\" onclick=updatePlay(1,"+id+")><i class=\"fas fa-download\"></i>&nbsp;Download</button><button type=\"button\" class=\"btn btn-info\" onclick=updatePlay(2,"+id+")><i class=\"fas fa-check-circle\"></i>&nbsp;Toggle Status</button></div>"

    document.getElementById("playerModalTitle").innerText = data["title"];
    document.getElementById("playerModalContent").innerHTML = infos;

    $('#playerModal').modal('show');
}

function updatePlay(type, id='')
{
    if(type == 1)
    {
        //download file
        let link = apiEndpoint+"tvs/getFile?idEpisode="+tvsE[id]['id']+"&token="+userToken;
        let win = window.open(link, '_blank');
        win.focus();
    }
    else if(type == 2)
    {
        //set episode as watched/unwatched
        httpGet(apiEndpoint+"tvs/toggleViewed?idEpisode="+tvsE[id]['id']+"&token="+userToken);
        notify("Episode status updated","success");
    }
    else if(type == 3)
    {
        //play transcoded file
        let subType = "";
        let audioSelect = document.querySelector("#audioSelect").value;
        let subtitlesSelect = document.querySelector("#subtitlesSelect").value;
        if(subtitlesSelect == "")
            subtitlesSelect = "-1"
        else
            subType = fileInfos['subtitles'][subtitlesSelect]["codec"]
        let subTxt = "1";
        if(subType == "hdmv_pgs_subtitle" || subType == "dvd_subtitle")
            subTxt = "0";

        httpGet(apiEndpoint+"transcoder/start?idEpisode="+tvsE[id]['id']+"&token="+userToken+"&audioStream="+audioSelect+"&subStream="+subtitlesSelect+"&subTxt="+subTxt);

        let link = apiEndpoint+"transcoder/m3u8?token="+userToken;
        showPlayer(false, link, id);
    }
    else if(type == 4)
    {
        //play file
        let link = apiEndpoint+"tvs/getFile?idEpisode="+tvsE[id]['id']+"&token="+userToken;
        showPlayer(true, link, id);
    }
    else if(type == 5)
    {
        //reload player
        let videoPlayer = videojs('videoPlayer');
        let url = videoPlayer.currentSrc()
        console.log(url)
        videoPlayer.dispose();

        document.querySelector("#player").innerHTML = '<video id="videoPlayer" class="video-js vjs-default-skin" controls preload="auto"></video>';
        const player = videojs('videoPlayer', {liveui: true});
            player.src({
            src: url,
            type: 'application/x-mpegURL'
        });
    }
}

function showPlayer(static, url, id)
{
    changePage(true);
    $('#playerModal').modal('hide');
    document.querySelector("#player").hidden = false;
    let data;
    
    document.querySelector("#userNavPlayerNext").innerHTML = "<button type=\"button\" class=\"btn btn-outline-warning btn-sm mx-1\" onclick=\"showPlay("+(id+1)+");\"><i class=\"fas fa-step-forward\"></i>&nbsp;Next</button>";
    document.querySelector("#userNavPlayerReload").hidden = false;

    playing = id;

    if(static)
    {
        data = '<video controls class="videoPlayer"><source src="'+url+'" type="video/mp4"><p>HTML5 video error</p></video>';
    }
    else
    {
        data = '<video id="videoPlayer" class="video-js vjs-default-skin" controls preload="auto"></video>';
        notify("Starting up conversion, please wait ...","info");

        setTimeout(function() 
        {
            const player = videojs('videoPlayer', {liveui: true});
                player.src({
                src: url,
                type: 'application/x-mpegURL'
            });
        }, 10000);//wait 10sec for conversion
    }
    document.querySelector("#player").innerHTML = data;
}

function checkPlaybackEnd()
{
    if(playing !== false)
    {
        try
        {
            videojs('videoPlayer').dispose();
        }
        catch (e)
        {
            console.log('videojs error')
        }
        document.querySelector("#player").innerHTML = "";
        httpGet(apiEndpoint+"tvs/playbackEnd?idEpisode="+tvsE[playing]['id']+"&token="+userToken, true);
        playing = false;
    }
}

function showSettings()
{
    changePage(true);
    document.querySelector("#content").hidden = false;

    let settingsData = "<br><button type=\"button\" class=\"btn btn-warning btn-lg btn-block\" onclick=\"settingsLibUpdate(0)\"><i class=\"fas fa-sync\"></i>&nbsp;Update Library</button><br>";
    
    let tvsData = JSON.parse(httpGet(apiEndpoint+"tvs/getShowsMultipleResults?token="+userToken));
    
    let i = 0;
    let cards = "";
    for(let tvsEntity of tvsData)
    {
        let dat = "<div class=\"row\"><div class=\"card\" id=\"settingsShow_"+tvsEntity["id"]+"\"><div class=\"card-header\"> TV Show "+tvsEntity["id"]+" ("+tvsEntity["path"]+")</div><div class=\"card-body\">"
        results = JSON.parse(tvsEntity["multipleResults"])
        for(let i=0; i<results.length; i++)
        {
            dat += "<div class=\"card text-white bg-dark\"><div class=\"row no-gutters\">"
            dat += "<img src=\""+results[i]["icon"]+"\" height=\"200px\" class=\"card-img col-2\">"
            dat += "<div class=\"card-body  col-10 pl-3\">"
            dat += "<h5 class=\"card-title\">"+results[i]["title"]+"</h5>"
            dat += "<p class=\"card-text\">Premiered: "+results[i]["premiered"]+" <br> Scraper: "+results[i]["scraperName"]+" <br> In Production: "+results[i]["in_production"]+"<br><small class=\"text-muted\">"+results[i]["desc"]+"</small></p>"
            dat += "<button type=\"button\" class=\"btn btn-success btn-lg btn-block\" onclick=settingsSelectShow("+tvsEntity['id']+","+i+")><i class=\"fas fa-check\"></i>&nbsp;Select</button>"
            dat += "</div></div></div>"
        }
        dat += "</div></div></div>";
        
        settingsData += '<br><br>'+dat;
        i++;
    }

    settingsData += "<br><br>";

    let logs = JSON.parse(httpGet(apiEndpoint+'logs?token='+userToken));    
    settingsData += "<div class=\"card\"><div class=\"card-header text-light bg-primary\">Logs</div><div class=\"card-body bg-dark\"><p class=\"card-text\">";
    for(let i=0; i<logs.length; i++)
    {
        let dat = logs[i];
        dat = dat.replace('INFO','<span class="text-success">INFO</span>')
        dat = dat.replace('DEBUG','<span class="text-info">DEBUG</span>')
        dat = dat.replace('WARNING','<span class="text-warning">WARNING</span>')
        dat = dat.replace('ERROR','<span class="text-danger">ERROR</span>')
        dat = dat.replace('CRITICAL','<span class="text-danger">CRITICAL</span>')
        let index = dat.indexOf('::');
        dat = '<span class="text-secondary">'+dat.substring(0, index)+'</span> :: <span class="text-light">'+dat.substring(index+2)+'</span><br>';
        settingsData += dat;
    }
    settingsData += "</p></div></div>";
    
    document.querySelector("#content").innerHTML = settingsData;
}

function settingsSelectShow(idShow, id)
{
    try
    {
        httpGet(apiEndpoint+"tvs/setID?idShow="+idShow+"&id="+id+"&token="+userToken, true);
        let card = document.querySelector("#settingsShow_"+idShow);
        card.parentNode.removeChild(card);
        notify("Preferences Applied","success")
    }
    catch (e)
    {
        notify("Unauthorized Action","error")
    }    
}

function settingsLibUpdate(type=0)
{
    if(type == 0)
    {
        httpGet(apiEndpoint+"tvs/runScan?token="+userToken,true);
        notify("Library Scan Started","success")
    }
    else if(type == 1)
    {
        httpGet(apiEndpoint+"tvs/syncKodi?token="+userToken,true);
        notify("Kodi Libray Sync Started","success")
    }
}