function checkPlaybackEnd()
{
    tvs_checkPlaybackEnd();
}

document.addEventListener('DOMContentLoaded', () => {

    window.addEventListener('hashchange', () => changePage());
    window.addEventListener("beforeunload",() => checkPlaybackEnd());
    document.querySelector("#logout").addEventListener('click', () => logout());
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

var apiEndpoint = "api/";
var fileInfos;
var userToken = null;

function changePageActive(id)
{
    let tabs = [
        document.querySelector("#homeNav"),
        document.querySelector("#tvshowsNav"),
        document.querySelector("#moviesNav"),
        document.querySelector("#musicNav"),
        document.querySelector("#gamesNav"),
        document.querySelector("#mangasNav"),
        document.querySelector("#booksNav"),
        document.querySelector("#devicesNav")
    ];
    for(let i=0; i<tabs.length; i++)
    {
        if(i == id)
            tabs[i].classList.add("active");
        else
            tabs[i].classList.remove("active");
    }
}

function clearPages()
{
    document.querySelector("#userNavPlayerNext").innerHTML = "";
    document.querySelector("#home").hidden = true;
    document.querySelector("#content").hidden = true;
    document.querySelector("#content").innerHTML = "";
    document.querySelector("#login").hidden = true;
}

function changePage(hash=null)
{
    if(hash == null)
    {
        hash = location.hash.slice(1);
    }
    else
    {
        if(history.pushState) {
            history.pushState(null, null, '#'+hash);
        }
        else {
            location.hash = '#'+hash;
        }
    }
    checkPlaybackEnd();
    clearPages();
    
    if(userToken == null)
    {
        //Show login screen
        changePageActive(-1);
        document.querySelector("#login").hidden = false;
    }
    else if(hash == "movies")
    {
        //show Movies
        changePageActive(2);
        document.querySelector("#content").hidden = false;
    }
    else if(hash == "tvshows")
    {
        //show TV Shows
        changePageActive(1);
        document.querySelector("#content").hidden = false;
        tvs_show();
    }
    else if(hash.indexOf("tvshow_") != -1)
    {
        //Show episodes for a TV Show
        changePageActive(1);
        document.querySelector("#content").hidden = false;
        tvs_showEpisodes(hash.substring(7));
    }
    else if(hash == "music")
    {
        //show Music
        changePageActive(3);
        document.querySelector("#content").hidden = false;
    }
    else if(hash == "games")
    {
        //show Games
        changePageActive(4);
        document.querySelector("#content").hidden = false;
    }
    else if(hash == "mangas")
    {
        //show Mangas
        changePageActive(5);
        document.querySelector("#content").hidden = false;
    }
    else if(hash == "books")
    {
        //show Books
        changePageActive(6);
        document.querySelector("#content").hidden = false;
    }
    else if(hash == "devices")
    {
        //show Devices screen
        changePageActive(7);
        document.querySelector("#content").hidden = false;
    }
    else if(hash == "settings")
    {
        //Show Settings screen
        changePageActive(-1);
        document.querySelector("#content").hidden = false;
        settings_show()
    }
    else if(hash == "player")
    {
        //Player screen
        changePageActive(-1);
        document.querySelector("#player").hidden = false;
    }
    else
    {
        //Show Home screen
        changePageActive(0);
        document.querySelector("#home").hidden = false;
        home_show();
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

function home_show()
{
    let userData = JSON.parse(httpGet(apiEndpoint+"users/data?token="+userToken));
    let stats = JSON.parse(httpGet(apiEndpoint+"core/getStatistics?token="+userToken));
    document.querySelector("#statsWatchedEP").textContent = stats["watchedEpCount"];
    document.querySelector("#statsLostTime").textContent = stats["lostTime"]+"H";
    document.querySelector("#statsAvTVS").textContent = stats["tvsCount"];
    document.querySelector("#statsAvEP").textContent = stats["epCount"];
    document.querySelector("#cardUserName").textContent = userData["name"];
    document.querySelector("#cardUserImg").setAttribute("src","../static/icons/"+userData["icon"]);
}


function settings_show()
{
    let settingsData = "<br><div class=\"btn-group btn-lg btn-block\">";
    settingsData += "<button type=\"button\" class=\"btn btn-warning\" onclick=\"settingsLibUpdate(0)\"><i class=\"fas fa-sync\"></i>&nbsp;Update Library</button>"
    settingsData += "<button type=\"button\" class=\"btn btn-warning\" onclick=\"settingsLibUpdate(1)\"><i class=\"fas fa-sync\"></i>&nbsp;Update Cache</button></div><br>";
        
    let cards = "";
    settingsData += "<br><br>"+tvs_makeSettingsCard();
    settingsData += "<br><br>"+mov_makeSettingsCard();

    settingsData += "<br><br>";

    let logs = JSON.parse(httpGet(apiEndpoint+'core/getLogs?token='+userToken));    
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

function settingsLibUpdate(type=0)
{
    if(type == 0)
    {
        httpGet(apiEndpoint+"core/runScan?token="+userToken,true);
        notify("Library Scan Started","success")
    }
    else if(type == 1)
    {
        httpGet(apiEndpoint+"core/refreshCache?token="+userToken,true);
        notify("Cache Refresh Started","success")
    }
    else if(type == 2)
    {
        httpGet(apiEndpoint+"tvs/syncKodi?token="+userToken,true);
        notify("Kodi Libray Sync Started","success")
    }
}