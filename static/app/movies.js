var movies;
var movPlaying = false;

function mov_show()
{
    movies = JSON.parse(httpGet(apiEndpoint+"movies/getMovies?token="+userToken));
    
    let i = 0;
    let cards = "";
    while(i<movies.length)
    {
        cards += mov_makeCard(i);
        i++;
    }
    document.querySelector("#content").innerHTML = "<div class=\"row\">"+cards+"</div>";
}


function mov_makeCard(id)
{
    let data = movies[id]    
    if(data["title"] == null)
        data["title"] = data["path"]
    if(data["genre"] == "null")
        data["genre"] = "[]"
    if(data["icon"] == null)
        data["icon"] = "static/icons/undefinedTVS.png"

    let descData = "<div class=\"btn-group btn-sm\" role=\"group\">"
    descData += "<a type=\"button\" class=\"btn btn-primary btn-sm\" onclick=\"mov_showPlay('"+id+"')\">Play</a>"
    descData += "<button type=\"button\" class=\"btn btn-info btn-sm\" onclick=\"mov_showInfo("+id+")\">Info</button>"
    if(data["viewCount"] > 0)
    {
        descData += "<button type=\"button\" class=\"btn btn-success disabled btn-sm\">Viewed <span class=\"badge badge-light\">"+data["viewCount"]+"</span></btn>";
    }
    else
    {
        descData += "<button type=\"button\" class=\"btn btn-danger disabled btn-sm\">Not Viewed</btn>";
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

function mov_showInfo(id)
{
    let data = movies[id];
    let infos = "Genre: "+JSON.parse(data["genre"]).join(" / ")+"<br/>"
    infos += "Premiered: "+data["premiered"]+"<br/>"
    infos += "Rating: "+data["rating"]+"<br/>"
    let scraperName = data["scraperLink"].match("(?:\\/\\/)([^\\/]*)(?=\\/)")[1]
    infos += "More Infos: <a target=\"_blank\" rel=\"noopener noreferrer\" href="+data["scraperLink"]+">"+scraperName+"</a><br/>"
    infos += "Description: <br/>"+data["overview"]
    document.getElementById("infoModalTitle").innerText = data["title"];
    document.getElementById("infoModalContent").innerHTML = infos;
    document.getElementById("cssContainer").innerHTML = ".modal-backdrop { background-image: url(\""+data["fanart"]+"\");background-size: cover;background-position: center center; background-repeat: no-repeat; background-attachment: fixed; position: fixed;}";
    $('#infoModal').modal('show');
}

function mov_showPlay()
{

}

function mov_makeSettingsCard()
{
    let moviesData = JSON.parse(httpGet(apiEndpoint+"movies/getShowsMultipleResults?token="+userToken))
    let settingsData = '';
    let i = 0;
    for(let movieEntity of moviesData)
    {
        let dat = "<div class=\"row\"><div class=\"card\" id=\"settingsMovie_"+movieEntity["id"]+"\"><div class=\"card-header\"> Movie "+movieEntity["id"]+" ("+movieEntity["path"]+")</div><div class=\"card-body\">"
        results = JSON.parse(movieEntity["multipleResults"])
        for(let i=0; i<results.length; i++)
        {
            dat += "<div class=\"card text-white bg-dark\"><div class=\"row no-gutters\">"
            dat += "<img src=\""+results[i]["icon"]+"\" height=\"200px\" class=\"card-img col-2\">"
            dat += "<div class=\"card-body  col-10 pl-3\">"
            dat += "<h5 class=\"card-title\">"+results[i]["title"]+"</h5>"
            dat += "<p class=\"card-text\">Premiered: "+results[i]["premiered"]+" <br> Scraper: "+results[i]["scraperName"]+"<br><small class=\"text-muted\">"+results[i]["desc"]+"</small></p>"
            dat += "<button type=\"button\" class=\"btn btn-success btn-lg btn-block\" onclick=mov_settingsSelect("+movieEntity['id']+","+i+")><i class=\"fas fa-check\"></i>&nbsp;Select</button>"
            dat += "</div></div></div>"
        }
        dat += "</div></div></div>";
        
        settingsData += '<br><br>'+dat;
        i++;
    }
    return settingsData;
}

function mov_settingsSelect(idMovie, id)
{
    try
    {
        httpGet(apiEndpoint+"movies/setID?idMovie="+idMovie+"&id="+id+"&token="+userToken, true);
        let card = document.querySelector("#settingsMovie_"+idMovie);
        card.parentNode.removeChild(card);
        notify("Preferences Applied","success")
    }
    catch (e)
    {
        notify("Error","error")
    }    
}
