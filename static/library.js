
document.addEventListener('DOMContentLoaded', () => {

    window.addEventListener('hashchange', () => changePage());
    changePage();

});

function httpGet(theUrl, sync=false)
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", theUrl, sync); // false for synchronous request
    xmlHttp.send( null );
    return xmlHttp.responseText;
}

var apiEndpoint = "http://192.168.1.9:5000/api/";
var tvshows;
var tvsE;
var userToken = null;

function changePage() 
{
    let hash = location.hash.slice(1);
    
    if(userToken == null)
    {
        document.querySelector("#homeNav").classList.remove("active");
        document.querySelector("#tvshowsNav").classList.remove("active");
        document.querySelector("#home").hidden = true;
        document.querySelector("#content").hidden = true;
        document.querySelector("#login").hidden = false;
        console.log("loutre");
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

function login()
{
    let user = document.querySelector("#login_user").value;
    let pass = document.querySelector("#login_password").value;
    let ret = httpGet(apiEndpoint+"users/authenticate?user="+user+"&password="+pass);
    try
    {
        userToken = JSON.parse(ret)["response"];
        changePage();
    }
    catch
    {
        alert("Authentification Failed");
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
        if(tvshows[i]["multipleResults"] == null)
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
    document.getElementById("movieInfoModalTitle").innerText = data["title"];
    document.getElementById("movieInfoModalContent").innerHTML = infos;
    document.getElementById("cssContainer").innerHTML = ".modal-backdrop { background-image: url(\""+data["fanart"]+"\");background-size: cover;background-position: center center; background-repeat: no-repeat; background-attachment: fixed; position: fixed;}";
    $('#movieInfoModal').modal('show');
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
    document.getElementById("content").innerHTML = cards;
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
    document.getElementById("movieInfoModalTitle").innerText = data["title"];
    document.getElementById("movieInfoModalContent").innerHTML = infos;
    document.getElementById("cssContainer").innerHTML = "";
    $('#movieInfoModal').modal('show');
}

