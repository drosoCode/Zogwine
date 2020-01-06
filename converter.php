<?php
/*
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
*/
$act = $_GET["action"];

if($act == "info")
{
    header('Content-Type: application/json');

    $file = $_GET["file"];
    if($file != "norefresh")
    {
        $file = base64_decode($file);
        $ext = substr($file, strrpos($file, '.', -0) + 1);
        $fileName = substr($file, strrpos($file, '/', -0) + 1);
        echo(exec("rm input.*"));
        echo(exec("smbget -o input.".$ext." \"".$file."\""));

        exec("./ffprobe.exe -v quiet -print_format json -show_format -show_streams input.".$ext." > data.json");
    }

    echo(json_encode(extractInfos()));
}
elseif($act == "convert")
{
    $file = "input.mkv";
    $audio = $_GET["audio_stream"];
    $sub = $_GET["subtitles_stream"];
    $stype = $_GET["subtitles_txt"];

    $outName = "out/stream";
    $crf = 20;

    if($stype != "1")
        $cmd = "./ffmpeg.exe -i ".$file." -pix_fmt yuv420p -preset medium -filter_complex \"[0:v][0:s:".$sub."]overlay[v]\" -map \"[v]\" -map 0:a:".$audio." -c:a aac -ar 48000 -b:a 128k -c:v h264_nvenc -crf ".$crf." -hls_time 120 -hls_playlist_type event -hls_segment_filename ".$outName."%03d.ts ".$outName.".m3u8";
    else
        $cmd = "./ffmpeg.exe -vsync 0 -i ".$file." -pix_fmt yuv420p -vf subtitles=".$file." -c:a aac -ar 48000 -b:a 128k -pix_fmt yuv420p -c:v h264_nvenc -map 0:a:".$audio." -map 0:v:0 -map 0:s:".$sub." -crf ".$crf." -hls_time 60 -hls_playlist_type event -hls_segment_filename ".$outName."%03d.ts ".$outName.".m3u8";
    #-c:v hevc_cuvid 
    $cmd = "nohup ".$cmd." &";
    echo($cmd);
    exec("rm out/*.ts");
    echo(exec($cmd));
}
elseif($act == "stop")
{
    echo(exec("sudo kill $(ps aux | grep ffmpeg | awk '{print $2}')"));
}
elseif($act == "ping")
{
    echo("pong");
}


function extractInfos()
{
    $data = json_decode(file_get_contents("data.json"), true);

    $retData = array("general" => array("format" => $data["format"]["format_long_name"], "duration" => $data["format"]["duration"]), "audio" => array(), "subtitles" => array());

    foreach($data["streams"] as $var)
    {
        if($var["codec_type"] == "video")
        {
            $retData["general"]["video_codec"] = $var["codec_name"]; 
        }
        elseif($var["codec_type"] == "audio")
        {
            array_push($retData["audio"], array("index" => $var["index"], "codec" => $var["codec_name"], "channels" => $var["channels"], "language" => $var["tags"]["language"]));
        }
        elseif($var["codec_type"] == "subtitle")
        {
            array_push($retData["subtitles"], array("index" => $var["index"], "codec" => $var["codec_name"], "language" => $var["tags"]["language"]));
        }
    }

    return $retData;
}

?>
