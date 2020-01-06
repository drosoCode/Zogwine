<?php

$query = $_GET["query"];

switch($query)
{
    case "list":
        $type = $_GET["type"];

        if(type == "tvs")
        {
            print_r(db_tvShowList())
        }
        elseif(type == "tvsEP")
        {
            $name = $_GET["name"];

        }

    break;

    case "getFileInfos":
        $file = $_GET["file"];

    break;

    case "startTranscode":
        $audio = $_GET["audioStream"];
        $sub = $_GET["subStream"];
        $subType = $_GET["subType"];
        $quality = $_GET["quality"];

    break;

    case "stopTranscode":

    break;
}


function db_tvShowList()
{
    $host = "192.168.1.12";
    $db = "ThomasVideo116";
    $db = new PDO('mysql:host='.$host.';dbname='.$db.';charset=utf8', 'kodi', 'kodi');

    $tvShowList = array();

    $request = 'SELECT c00 AS "title",
                    idShow AS "id",
                    c01 AS "desc",
                    c05 AS "premiered",
                    c08 AS "genre",
                    c14 AS "studio",
                    rating,
                    totalSeasons AS "seasons",
                    totalCount AS "episodes",
                    watchedcount AS "viewedEpisodes",
                    uniqueid_type,
                    uniqueid_value AS "scraperLink",
                    c06 AS "icon",
                    c11 AS "fanart"
                FROM tvshow_view 
                ORDER BY c00;';

    $reponse = $bdd->query($request)->fetchall();

    foreach($reponse as &$tvs)
    {
        preg_match("(?:<thumb aspect=\"poster\" \S*\">)(\S*)(?=<\/thumb>)\\S*(?=<\\/thumb>)", $tvs["icon"], $buf);
        $tvs["icon"] = $buf[0];

        preg_match("(?:<thumb \S*\">)(\S*)(?=<\/thumb>)\\S*(?=<\\/thumb>)", $tvs["fanart"], $buf);
        $tvs["fanart"] = $buf[0];

        $tvs["scraperLink"] = getScarperLink($tvs["uniqueid_type"], $tvs["scraperLink"]);
        unset($tvs["uniqueid_type"]);
    }
    return $reponse;
}


function db_tvShowEpisodeList($idShow)
{
    $host = "192.168.1.12";
    $db = "ThomasVideo116";
    $db = new PDO('mysql:host='.$host.';dbname='.$db.';charset=utf8', 'kodi', 'kodi');

    $tvShowList = array();
    $tvShowSeason = array();

    $request = 'SELECT c00 AS "title",
                    c01 AS "desc",
                    c05 AS "premiered",
                    c12 AS "season",
                    c13 AS "episode",
                    c18 AS "path",
                    playCount AS "viewed",
                    rating,
                    uniqueid_type,
                    uniqueid_value AS "scraperLink",
                    c06 AS "icon"
                FROM episode_view 
                ORDER BY c12, c13;';

    $reponse = $bdd->query($request)->fetchall();

    $currentSeason = $reponse[0]["season"];
    foreach($reponse as $tvs)
    {
        if($tvs["season"] != $currentSeason)
        {
            array_push($tvShowList, $tvShowSeason);
            $tvShowSeason = array();
            $currentSeason = $tvs["season"];
        }


        preg_match("(?:<thumb>)(\\S*)(?=<\\/thumb>)\S*(?=<\\/thumb>)", $tvs["icon"], $buf);
        $tvs["icon"] = $buf[0];

        $tvs["scraperLink"] = getScarperLink($tvs["uniqueid_type"], $tvs["scraperLink"]);
        unset($tvs["uniqueid_type"]);

        array_push($tvShowSeason, $tvs);
    }
    return $tvShowList;
}

function getScarperLink($type, $id)
{
    switch($type)
    {
        if($type == "tmdb")
            return "https://www.themoviedb.org/movie/".$id;
        else if($type == "imdb")
            return "https://www.imdb.com/title/".$id;
        else if($type == "tvdb")
            return = "https://thetvdb.com/?tab=series&id=".$id;
        else
            return "-1";
    }
}

?>