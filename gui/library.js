
function showHome()
{
    document.getElementById("home").style = "";
    document.getElementById("content").style = "display:none;";
}

function showPlay(type,id)
{
    if(type == 1)
    {
        data = movies[id];
    }
    content = "";
    document.getElementById("cssContainer").innerHTML = ".modal-backdrop { background-image: url(\""+data["fanart"]+"\");background-size: cover;}";
    document.getElementById("playerModalTitle").innerText = data["title"];
    document.getElementById("playerModalContent").innerText = content;
    $('#playerModal').modal('show');
}

function showTVS()
{
    document.getElementById("home").style = "display:none;";
    document.getElementById("content").style = "";
    i = 0;
    cards = "";
    while(i<tvshows.length)
    {
        cards += makeTVSCard(i);
        i++;
    }
    document.getElementById("content").innerHTML = "<div class=\"row\">"+cards+"</div>";
}

function makeTVSCard(id)
{
    data = tvshows[id]
    descData = "<div class=\"btn-group btn-sm\" role=\"group\">"
    descData += "<button type=\"button\" class=\"btn btn-primary btn-sm\" onclick=\"showTVSEpisodes("+id+")\">Play</button>"
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

    card = "<div class=\"col-xl-3 col-lg-6 col-md-6 col-sm-12 col-xs-12\">"
    card += "<div class=\"card text-white bg-dark\">"
        card += "<div class=\"row no-gutters\">"
                card += "<img src=\""+data["icon"]+"\" height=\"200px\" class=\"card-img col-4\" onclick=\"showTVSEpisodes("+id+")\">"
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
    data = tvshows[id];
    infos = "Genre: "+data["genre"]+"<br/>"
    infos += "Studio: "+data["studio"]+"<br/>"
    infos += "Premiered: "+data["premiered"]+"<br/>"
    infos += "Rating: "+data["rating"]+"<br/>"
    infos += "Episodes: "+data["episodes"]+"<br/>"
    infos += "Viewed Episodes: "+data["viewedEpisodes"]+"<br/>"
    scraperName = data["scraperLink"].substring(0,data["scraperLink"].indexOf(".com")+4)
    infos += "More Infos: <a target=\"_blank\" rel=\"noopener noreferrer\" href="+data["scraperLink"]+">"+scraperName+"</a><br/>"
    infos += "Description: <br/>"+data["desc"]
    document.getElementById("movieInfoModalTitle").innerText = data["title"];
    document.getElementById("movieInfoModalContent").innerHTML = infos;
    document.getElementById("cssContainer").innerHTML = ".modal-backdrop { background-image: url(\""+data["fanart"]+"\");background-size: cover;background-position: center center; background-repeat: no-repeat; background-attachment: fixed; position: fixed;}";
    $('#movieInfoModal').modal('show');
}


function showTVSEpisodes(id)
{
    document.getElementById("home").style = "display:none;";
    document.getElementById("content").style = "";
    id = tvshows[id]["id"];
    tvsE = tvsData[id.toString()];
    cards = "";
    i = 0;
    seasons = Object.keys(tvsE);
    while(i<seasons.length)
    {
        episodes = tvsE[seasons[i]]
        j = 0;
        cards += "<div class=\"alert alert-dark mt-4\" role=\"alert\">"
            cards += "Season "+seasons[i]
        cards += "</div>"
        cards += "<div class=\"row\">"
        while(j<episodes.length)
        {
            cards += makeTVSEpisodesCard(id,seasons[i],j);
            j++;
        }
        cards += "</div>"
        i++;
    }
    document.getElementById("content").innerHTML = cards;
}


function makeTVSEpisodesCard(idShow,idSeason,idEpisode)
{
    data = tvsData[idShow.toString()][idSeason][idEpisode];
    id = idShow+"."+idSeason+"."+idEpisode;
    descData = "<div class=\"btn-group btn-sm\" role=\"group\">"
    descData += "<button type=\"button\" class=\"btn btn-primary btn-sm\" onclick=\"showPlay(2,'"+id+"')\">Play</button>"
    descData += "<button type=\"button\" class=\"btn btn-info btn-sm\" onclick=\"showTVSEpisodeInfo('"+id+"')\">Info</button>"
    if(data["viewed"] > 0)
    {
        descData += "<button type=\"button\" class=\"btn btn-success disabled btn-sm\">Viewed <span class=\"badge badge-light\">"+data["viewed"]+"</span></btn>";
    }
    else
    {
        descData += "<button type=\"button\" class=\"btn btn-danger disabled btn-sm\">Not Viewed</btn>";
    }
    descData += "</div>"

    card = "<div class=\"col-xl-3 col-lg-4 col-md-6 col-sm-6 col-xs-12\">"
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
    id = id.split(".");
    data = tvsData[id[0]][id[1]][id[2]];
    infos = "Season: "+data["season"]+"<br/>"
    infos += "Episode: "+data["episode"]+"<br/>"
    infos += "Premiered: "+data["premiered"]+"<br/>"
    infos += "Rating: "+data["rating"]+"<br/>"
    scraperName = data["scraperLink"].substring(0,data["scraperLink"].indexOf(".com")+4)
    infos += "More Infos: <a target=\"_blank\" rel=\"noopener noreferrer\" href="+data["scraperLink"]+">"+scraperName+"</a><br/>"
    infos += "Description: <br/>"+data["desc"]
    document.getElementById("movieInfoModalTitle").innerText = data["title"];
    document.getElementById("movieInfoModalContent").innerHTML = infos;
    document.getElementById("cssContainer").innerHTML = "";
    $('#movieInfoModal').modal('show');
}

