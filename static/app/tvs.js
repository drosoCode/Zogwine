var tvshows;
var tvsE;
var tvsPlaying = false;

function tvs_show()
{
    tvshows = JSON.parse(httpGet(apiEndpoint+"tvs/getShows?token="+userToken));
    
    let i = 0;
    let cards = "";
    while(i<tvshows.length)
    {
        cards += tvs_makeCard(i);
        i++;
    }
    document.querySelector("#content").innerHTML = "<div class=\"row\">"+cards+"</div>";
}

function tvs_makeCard(id)
{
    let data = tvshows[id]    
    if(data["title"] == null)
        data["title"] = data["path"]
    if(data["genre"] == "null")
        data["genre"] = "[]"
    if(data["icon"] == null)
        data["icon"] = "static/icons/undefinedTVS.png"

    let descData = "<div class=\"btn-group btn-sm\" role=\"group\">"
    descData += "<a type=\"button\" class=\"btn btn-primary btn-sm\" href=\"#tvshow_"+data["id"]+"\">Play</a>"
    descData += "<button type=\"button\" class=\"btn btn-info btn-sm\" onclick=\"tvs_showInfo("+id+")\">Info</button>"
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

function tvs_showInfo(id)
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

function tvs_showEpisodes(id)
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
                cards += "<button type=\"button\" class=\"btn btn-sm btn-outline-info mx-4\" onclick=tvs_seasonOptions(0,"+id+","+tvsE[i]["season"]+")><i class=\"fas fa-check-circle\"></i>&nbsp;Toggle Status</button>"
                cards += "<button type=\"button\" class=\"btn btn-sm btn-outline-warning mx-4\" onclick=tvs_seasonOptions(1,"+id+","+tvsE[i]["season"]+")><i class=\"fas fa-download\"></i>&nbsp;Download</button>"
            cards += "</div>"
            cards += "<div class=\"row\">"

            season = tvsE[i]["season"];
        }
        cards += tvs_makeEpisodesCard(i);
        i++;
    }
    document.getElementById("content").innerHTML = cards;
}

function tvs_seasonOptions(type, id, season)
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

function tvs_makeEpisodesCard(id)
{
    let data = tvsE[id];
    if(data["icon"] == null)
        data["icon"] = "static/icons/undefinedEp.png"

    let descData = "<div class=\"btn-group btn-sm\" role=\"group\">"
    descData += "<button type=\"button\" class=\"btn btn-primary btn-sm\" onclick=\"tvs_showPlay('"+id+"')\">Play</button>"
    descData += "<button type=\"button\" class=\"btn btn-info btn-sm\" onclick=\"tvs_showEpisodeInfo('"+id+"')\">Info</button>"
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

function tvs_showEpisodeInfo(id)
{
    let data = tvsE[id];
    let infos = "Season: "+data["season"]+"<br/>"
    infos += "Episode: "+data["episode"]+"<br/>"
    infos += "Premiered: "+data["premiered"]+"<br/>"
    infos += "Rating: "+data["rating"]+"<br/>"
    infos += "Description: <br/>"+data["overview"]
    document.querySelector("#infoModalTitle").innerText = data["title"];
    document.querySelector("#infoModalContent").innerHTML = infos;
    document.querySelector("#cssContainer").innerHTML = "";
    $('#infoModal').modal('show');
}

function tvs_showPlay(id)
{
    checkPlaybackEnd();
    let data = tvsE[id];
    fileInfos = JSON.parse(httpGet(apiEndpoint+"tvs/fileInfos?idEpisode="+data["id"]+"&token="+userToken));

    let infos = "<button type=\"button\" class=\"btn btn-primary\"><i class=\"fas fa-burn\"></i>&nbsp;Video Codec&nbsp;<span class=\"badge badge-light\">"+fileInfos['general']['video_codec']+"</span></button>";
    infos += "&nbsp;<button type=\"button\" class=\"btn btn-primary\"><i class=\"fas fa-barcode\"></i>&nbsp;Video Format&nbsp;<span class=\"badge badge-light\">"+fileInfos['general']['format']+"</span></button>";
    infos += "&nbsp;<button type=\"button\" class=\"btn btn-primary\"><i class=\"fas fa-clock\"></i>&nbsp;Duration&nbsp;<span class=\"badge badge-light\">"+Math.round(fileInfos['general']['duration']/60)+" mins</span></button>";

    document.getElementById("playerModalTitle").innerText = data["title"];

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

            infos += "</div><br>"
            let startFrom = Math.round(fileInfos['general']['startFrom']/60);
            let duration = Math.round(fileInfos['general']['duration']/60);

            infos += "<div class=\"form-row\">"
            infos += "<div class=\"col mt-4 ml-3\"><input type='text' data-slider-id='startFromSliderContent' data-slider-min='0' data-slider-max='"+duration+"' data-slider-step='1' data-slider-value='"+startFrom+"' id='startFromSlider' data-slider-tooltip='hide' data-slider-handle='round' /><span>&nbsp;&nbsp;Start from: <span id='startFromSliderVal'>"+startFrom+"</span> mins</span></div>";
            infos += "<div class=\"col\"><label for=\"resizeSelect\">Resize</label><select class=\"form-control\" id=\"resizeSelect\"><option value=0 selected>Original</option><option value=1080>1080</option><option value=720>720</option><option value=480>480</option><option value=320>320</option></select></div>";
            infos += "</div>"

        infos += "<br><br><button type=\"button\" class=\"btn btn-outline-success btn-block\" onclick=tvs_updatePlay(3,"+id+")><i class=\"fas fa-play-circle\"></i>&nbsp;Play</button>";
        infos += "<br><div class=\"btn-group btn-block\" role=\"group\"><button type=\"button\" class=\"btn btn-warning\" onclick=tvs_updatePlay(1,"+id+")><i class=\"fas fa-download\"></i>&nbsp;Download</button><button type=\"button\" class=\"btn btn-info\" onclick=updatePlay(2,"+id+")><i class=\"fas fa-check-circle\"></i>&nbsp;Toggle Status</button></div>"

        document.getElementById("playerModalContent").innerHTML = infos;

        var slider = new Slider("#startFromSlider");
        slider.on("slide", function(sliderValue) {
            document.querySelector("#startFromSliderVal").textContent = sliderValue;
        });
    }
    else
    {
        infos += "<br><br><button type=\"button\" class=\"btn btn-outline-success btn-block\" onclick=tvs_updatePlay(4,"+id+")><i class=\"fas fa-play-circle\"></i>&nbsp;Play</button>";
        infos += "<br><div class=\"btn-group btn-block\" role=\"group\"><button type=\"button\" class=\"btn btn-warning\" onclick=tvs_updatePlay(1,"+id+")><i class=\"fas fa-download\"></i>&nbsp;Download</button><button type=\"button\" class=\"btn btn-info\" onclick=updatePlay(2,"+id+")><i class=\"fas fa-check-circle\"></i>&nbsp;Toggle Status</button></div>"
        document.getElementById("playerModalContent").innerHTML = infos;
    }
    
    $('#playerModal').modal('show');
}

function tvs_updatePlay(type, id='')
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
        httpGet(apiEndpoint+"tvs/toggleViewedEp?idEpisode="+tvsE[id]['id']+"&token="+userToken);
        notify("Episode status updated","success");
    }
    else if(type == 3)
    {
        //play transcoded file
        let subType = "";
        let audioSelect = document.querySelector("#audioSelect").value;
        let subtitlesSelect = document.querySelector("#subtitlesSelect").value;
        let resizeSelect = document.querySelector("#resizeSelect").value;
        if(subtitlesSelect == "")
            subtitlesSelect = "-1"
        else
            subType = fileInfos['subtitles'][subtitlesSelect]["codec"]
        let subTxt = "1";
        if(subType == "hdmv_pgs_subtitle" || subType == "dvd_subtitle")
            subTxt = "0";
        
        let startFrom = parseInt(document.getElementById("startFromSliderVal").textContent, 10) * 60; //get startFrom in seconds

        httpGet(apiEndpoint+"transcoder/start?idEpisode="+tvsE[id]['id']+"&token="+userToken+"&audioStream="+audioSelect+"&subStream="+subtitlesSelect+"&subTxt="+subTxt+"&startFrom="+startFrom+"&resize="+resizeSelect);

        let link = apiEndpoint+"transcoder/m3u8?token="+userToken;
        tvs_showPlayer(false, link, id);
    }
    else if(type == 4)
    {
        //play file
        let link = apiEndpoint+"tvs/getFile?idEpisode="+tvsE[id]['id']+"&token="+userToken;
        tvs_showPlayer(true, link, id);
    }
}

function tvs_showPlayer(static, url, id)
{
    changePage("player");
    $('#playerModal').modal('hide');
    
    document.querySelector("#userNavPlayerNext").innerHTML = "<button type=\"button\" class=\"btn btn-outline-warning btn-sm mx-1\" onclick=\"tvs_showPlay("+(id+1)+");\"><i class=\"fas fa-step-forward\"></i>&nbsp;Next</button>";

    tvsPlaying = id;

    if(static)
    {
        document.querySelector("#player").innerHTML = '<video controls class="videoPlayer"><source src="'+url+'" type="video/mp4"><p>HTML5 video error</p></video>';
    }
    else
    {
        //display loading screen
        document.querySelector("#player").innerHTML = '<div id="loadingScreen" class="row d-flex justify-content-center vh-100" style="background-color: rgba(7, 7, 7, 0.5);"><div class="col-1 align-self-center"><div class="text-center font-weight-bold text-primary"><div class="text-center spinner-border text-primary" role="status"></div><br>Loading</div></div></div>';
        
        //wait until video is available
        var interval = setInterval(function()
        {
            var xmlHttp = new XMLHttpRequest();
            xmlHttp.open("GET", url, false);
            xmlHttp.send( null );
            if(xmlHttp.status != 404)
            {
                clearInterval(interval);
                document.querySelector("#player").innerHTML = '<video id="videoPlayer" class="video-js vjs-default-skin" controls preload="auto"></video>';
                const player = videojs('videoPlayer', {liveui: true, autoplay: true});
                    player.src({
                    src: url,
                    type: 'application/x-mpegURL'
                });
            }
            if(document.querySelector("#loadingScreen") === null)
            {
                clearInterval(interval);
            }
        }, 8000);
    }
}

function tvs_checkPlaybackEnd()
{
    if(tvsPlaying !== false)
    {
        try
        {
            videojs('videoPlayer').dispose();
            //for videos with transcoder
            httpGet(apiEndpoint+"tvs/playbackEnd?idEpisode="+tvsE[tvsPlaying]['id']+"&token="+userToken, true);
        }
        catch (e)
        {
            //for mp4 videos
            httpGet(apiEndpoint+"tvs/playbackEnd?idEpisode="+tvsE[tvsPlaying]['id']+"&token="+userToken+"&endTime="+document.querySelector(".videoPlayer").currentTime, true);
        }

        document.querySelector("#player").innerHTML = "";
        tvsPlaying = false;
    }
}


function tvs_makeSettingsCard()
{
    let tvsData = JSON.parse(httpGet(apiEndpoint+"tvs/getShowsMultipleResults?token="+userToken));
    let settingsData = '';
    let i = 0;
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
            dat += "<button type=\"button\" class=\"btn btn-success btn-lg btn-block\" onclick=tvs_settingsSelect("+tvsEntity['id']+","+i+")><i class=\"fas fa-check\"></i>&nbsp;Select</button>"
            dat += "</div></div></div>"
        }
        dat += "</div></div></div>";
        
        settingsData += '<br><br>'+dat;
        i++;
    }
    return settingsData;
}


function tvs_settingsSelect(idShow, id)
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
        notify("Error","error")
    }
}
