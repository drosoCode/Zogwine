<?php
/*
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
*/
header('Content-Type: application/json');

$query = $_GET["query"];

switch($query)
{
    case "list":
        $type = $_GET["type"];

        $db = new PDO('mysql:host=192.168.1.12;dbname=ThomasVideo116;charset=utf8', 'kodi', 'kodi');

        if($type == "tvs")
        {
            echo(json_encode(db_tvShowList($db)));
        }
        elseif($type == "tvsEP")
        {
            $id = $_GET["idShow"];
            echo(json_encode(db_tvShowEpisodeList($db, $id)));
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


function db_tvShowList($db)
{
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

    $reponse = $db->query($request)->fetchAll(PDO::FETCH_ASSOC);

    foreach($reponse as &$tvs)
    {
        preg_match("/(?:<thumb aspect=\"poster\" \\S*\">)(\\S*)(?=<\\/thumb>)/", $tvs["icon"], $buf);
        $tvs["icon"] = $buf[1];

        preg_match("/(?:<thumb \\S*\">)(\\S*)(?=<\\/thumb>)\\S*(?=<\\/thumb>)/", $tvs["fanart"], $buf);
        $tvs["fanart"] = $buf[1];

        $tvs["scraperLink"] = getScarperLink($tvs["uniqueid_type"], $tvs["scraperLink"]);
        unset($tvs["uniqueid_type"]);
    }
    return $reponse;
}


function db_tvShowEpisodeList($db, $idShow)
{
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
                WHERE idShow = ?
                ORDER BY c12, c13;';

    $reponse = $db->prepare($request);
    $reponse->execute([$idShow]);
    $reponse = $reponse->fetchAll(PDO::FETCH_ASSOC);

    $currentSeason = $reponse[0]["season"];
    foreach($reponse as $tvs)
    {
        if($tvs["season"] != $currentSeason)
        {
            array_push($tvShowList, $tvShowSeason);
            $tvShowSeason = array();
            $currentSeason = $tvs["season"];
        }

        preg_match("/(?:<thumb>)(\\S*)(?=<\\/thumb>)\S*(?=<\\/thumb>)/", $tvs["icon"], $buf);
        $tvs["icon"] = $buf[1];

        $tvs["scraperLink"] = getScarperLink($tvs["uniqueid_type"], $tvs["scraperLink"]);
        unset($tvs["uniqueid_type"]);

        array_push($tvShowSeason, $tvs);
    }
    return $tvShowList;
}

function getScarperLink($type, $id)
{
        if($type == "tmdb")
            return "https://www.themoviedb.org/movie/".$id;
        else if($type == "imdb")
            return "https://www.imdb.com/title/".$id;
        else if($type == "tvdb")
            return "https://thetvdb.com/?tab=series&id=".$id;
        else
            return "-1";
 }

?>
