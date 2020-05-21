function checkPlaybackEnd()
{
    tvs_checkPlaybackEnd();
}

document.addEventListener('DOMContentLoaded', () => {

    window.addEventListener('hashchange', () => changePage());
    window.addEventListener("beforeunload",() => checkPlaybackEnd());
    document.querySelector("#logout").addEventListener('click', () => logout());
    document.querySelector("#userNavSettings").addEventListener('click', () => showSettings());
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
        tvs_showEpisodes(hash.substring(7));
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
    let stats = JSON.parse(httpGet(apiEndpoint+"core/getStatistics?token="+userToken));
    document.querySelector("#statsWatchedEP").textContent = stats["watchedEpCount"];
    document.querySelector("#statsLostTime").textContent = stats["lostTime"]+"H";
    document.querySelector("#statsAvTVS").textContent = stats["tvsCount"];
    document.querySelector("#statsAvEP").textContent = stats["epCount"];
    document.querySelector("#cardUserName").textContent = userData["name"];
    document.querySelector("#cardUserImg").setAttribute("src","../static/icons/"+userData["icon"]);
}


function showSettings()
{
    changePage(true);
    document.querySelector("#content").hidden = false;

    let settingsData = "<br><div class=\"btn-group btn-lg btn-block\">";
    settingsData += "<button type=\"button\" class=\"btn btn-warning\" onclick=\"settingsLibUpdate(0)\"><i class=\"fas fa-sync\"></i>&nbsp;Update Library</button>"
    settingsData += "<button type=\"button\" class=\"btn btn-warning\" onclick=\"settingsLibUpdate(1)\"><i class=\"fas fa-sync\"></i>&nbsp;Update Cache</button></div><br>";
        
    let cards = "";
    settingsData += "<br><br>"+tvs_makeSettingsCard(JSON.parse(httpGet(apiEndpoint+"tvs/getShowsMultipleResults?token="+userToken)));
    settingsData += "<br><br>"+mov_makeSettingsCard(JSON.parse(httpGet(apiEndpoint+"movie/getShowsMultipleResults?token="+userToken)));

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