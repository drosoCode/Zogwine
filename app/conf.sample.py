sqlConnectionData = {
    "host": "mariadb",
    "user": "",
    "password": "",
    "database": "",
    "use_unicode": True,
    "charset": "utf8",
}

configData = {
    "redis": {
        "host": "redis",
        "port": 6379,
        "filesDB": 0,
        "usersDB": 1,
        "threadsDB": 2,
    },
    "api": {
        "tmdb": "",
        "tvdb": "",
    },
    "config": {
        "tvsDirectory": "/home/server/content/Series",
        "moviesDirectory": "/home/server/content/Movies",
        "crf": 23,
        "hlsTime": 60,
        "encoder": "h264_nvenc",
        "outDir": "/home/server/out/",
        "watchedThreshold": 0.9,
    },
}
