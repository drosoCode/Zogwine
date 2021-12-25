import youtube_dl
from app.log import logger


def getInfos(url):
    return "some infos"


def getUrl(url):
    logger.debug("Parsing source url for " + url)

    if (url[-4:] in (".avi", ".mkv", ".mp4", ".mp3")) or (".googlevideo.com/" in url):
        logger.debug("Direct video URL, no need to use youtube-dl.")
        return url

    ydl = youtube_dl.YoutubeDL(
        {
            "logger": logger,
            "noplaylist": True,
            "ignoreerrors": True,
        }
    )  # Ignore errors in case of error in long playlists
    with ydl:  # Downloading youtub-dl infos. We just want to extract the info
        result = ydl.extract_info(url, download=False)

    if result is None:
        logger.error("Result is none, returning none. Cancelling following function.")
        return None

    if "entries" in result:  # Can be a playlist or a list of videos
        video = result["entries"][0]
    else:
        video = result  # Just a video

    if "youtu" in url:
        logger.debug(
            """CASTING: Youtube link detected. Extracting url in maximal quality."""
        )
        for fid in ("22", "18", "36", "17"):
            for i in video["formats"]:
                if i["format_id"] == fid:
                    logger.debug(
                        "CASTING: Playing highest video quality "
                        + i["format_note"]
                        + "("
                        + fid
                        + ")."
                    )
                    return i["url"]
    elif "vimeo" in url:
        logger.debug("Vimeo link detected, extracting url in maximal quality.")
        return video["url"]
    else:
        logger.debug(
            """Video not from Youtube or Vimeo. Extracting url in maximal quality."""
        )
        return video["url"]
