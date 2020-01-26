
document.addEventListener('DOMContentLoaded', () => {

    window.addEventListener('hashchange', () => changePage());
    document.querySelector("#logout").addEventListener('click', () => logout());
    document.querySelector("#userNavSettings").addEventListener('click', () => showSettings());
    changePage();
    
});

function httpGet(url, sync=false)
{
    
    if(url.indexOf("?") >= 0)
        url += "&time="+new Date().getTime()
    else
        url += "?time="+new Date().getTime()
        
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", url, sync); // false for synchronous request
    xmlHttp.send( null );
    return xmlHttp.responseText;
}

//var apiEndpoint = "http://192.168.1.9:8080/api/";
var apiEndpoint = "api/";
var tvshows;
var tvsE;
var userToken = null;

function changePage(clear=false) 
{
    let hash = location.hash.slice(1);
    
    if(userToken == null)
    {
        document.querySelector("#homeNav").classList.remove("active");
        document.querySelector("#tvshowsNav").classList.remove("active");
        document.querySelector("#home").hidden = true;
        document.querySelector("#content").hidden = true;
        document.querySelector("#login").hidden = false;
        document.querySelector("#userNav").hidden = true;
        console.log("loutre");
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

function logout()
{
    userToken = null;
    document.querySelector("#login_user").value = '';
    document.querySelector("#login_password").value = '';
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
    catch
    {
        notify("Authentification Failed","error");
    }
}

function showPlay(id)
{
    let content = "<div class=\"progress\"><div class=\"progress-bar progress-bar-striped progress-bar-animated\" role=\"progressbar\" aria-valuenow=\"100\" aria-valuemin=\"0\" aria-valuemax=\"100\" style=\"width: 100%\">Connecting to Server ...</div></div>";
   
    document.getElementById("cssContainer").innerHTML = ".modal-backdrop { background-image: url(\""+data["fanart"]+"\");background-size: cover;}";
    document.getElementById("playerModalTitle").innerText = data["title"];
    document.getElementById("playerModalContent").innerHTML = content;
    $('#playerModal').modal('show');

    id = id.split(".");
    let link = tvsE[id[1]][id[2]]["link"];
    let infos = JSON.parse(httpGet(apiEndpoint+"fileInfos?idEpisode="+link));
    console.log(infos);
}

function showTVS()
{
    tvshows = JSON.parse(httpGet(apiEndpoint+"tvs/getShows"));
    
    let i = 0;
    let cards = "";
    while(i<tvshows.length)
    {
        if(tvshows[i]["title"] != null)
            cards += makeTVSCard(i);
        i++;
    }
    document.querySelector("#content").innerHTML = "<div class=\"row\">"+cards+"</div><br><br>";
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
    tvsE = JSON.parse(httpGet(apiEndpoint+"tvs/getEpisodes?idShow="+id));
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
            cards += "</div>"
            cards += "<div class=\"row\">"

            season = tvsE[i]["season"];
        }
        cards += makeTVSEpisodesCard(i,tvsE[i]);
        i++;
    }
    document.getElementById("content").innerHTML = cards+'<br><br>';
}


function makeTVSEpisodesCard(id,data)
{
    let descData = "<div class=\"btn-group btn-sm\" role=\"group\">"
    descData += "<button type=\"button\" class=\"btn btn-primary btn-sm\" onclick=\"showPlay('"+id+"')\">Play</button>"
    descData += "<button type=\"button\" class=\"btn btn-info btn-sm\" onclick=\"showTVSEpisodeInfo('"+id+"')\">Info</button>"
    if(data["viewCount"] > 0)
    {
        descData += "<button type=\"button\" class=\"btn btn-success disabled btn-sm\">Viewed <span class=\"badge badge-light\">"+data["viewed"]+"</span></btn>";
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
    let data = tvsE[id];
    let fileInfos = JSON.parse(httpGet(apiEndpoint+"tvs/fileInfos?idEpisode="+data["id"]));
    console.log(fileInfos);
    let infos = '';
    //fileInfos['general']['format'].indexOf()
    
    document.getElementById("playerModalTitle").innerText = data["title"];
    document.getElementById("playerModalContent").innerHTML = infos;
    document.getElementById("cssContainer").innerHTML = "";
    $('#playerModal').modal('show');
}


function showSettings()
{
    changePage(true);
    document.querySelector("#content").hidden = false;

    let settingsData = "<br><button type=\"button\" class=\"btn btn-warning btn-lg btn-block\" onclick=\"settingsLibUpdate(0)\"><i class=\"fas fa-sync\"></i>&nbsp;Update Library</button><br>";
    
    let tvsData = JSON.parse(httpGet(apiEndpoint+"tvs/getShowsMultipleResults"));
    
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
    catch
    {
        notify("Unauthorized Action","error")
    }    
}

function settingsLibUpdate(type=0)
{
    if(type == 0)
    {
        httpGet(apiEndpoint+"tvs/runScan",true);
        notify("Library Scan Started","success")
    }
    else if(type == 1)
    {
        httpGet(apiEndpoint+"tvs/syncKodi",true);
        notify("Kodi Libray Sync Started","success")
    }
}