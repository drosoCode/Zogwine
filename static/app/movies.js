var movies;
var tvsE;
var tvsPlaying = false;

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
