<?php

$db = 
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

}

?>