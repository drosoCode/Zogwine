package file

import (
	"context"
	"net/http"
	"path/filepath"
	"strconv"
	"strings"
	"sync"

	"github.com/Zogwine/Zogwine/internal/database"
	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util"
)

func ScanCache(s *status.Status) error {
	s.Log.Info("starting cache scan")

	data, err := s.DB.ListNotCached(context.Background())

	sem := make(chan struct{}, 10)
	var wg sync.WaitGroup

	if err != nil {
		return err
	}
	path := s.Config.Server.CachePath

	for _, item := range data {
		wg.Add(1)
		sem <- struct{}{}
		go func(s *status.Status, item database.Cache, path string) {
			defer wg.Done()
			CacheItem(s, item, path)
			<-sem
		}(s, item, path)
	}
	wg.Wait()
	close(sem)

	s.Log.Info("finished cache scan")
	return nil
}

func CacheItem(s *status.Status, item database.Cache, path string) error {
	files := []string{"jpg", "png", "gif", "webp", "bmp", "webm", "mp4", "mkv"}
	ext := item.Link[strings.LastIndex(item.Link, ".")+1:]
	var err error

	s.Log.Tracef("caching link: %s", item.Link)

	if util.Contains(files, ext) {
		util.DownloadFile(item.Link, filepath.Join(path, strconv.Itoa(int(item.ID))+"."+ext))
	} else {
		response, err := http.Get(item.Link)
		if err == nil {
			contentType := response.Header.Get("Content-Type")
			if contentType[0:6] == "image/" || contentType[0:6] == "video/" {
				err = util.DownloadFile(item.Link, filepath.Join(path, strconv.Itoa(int(item.ID))+"."+ext))
			} else if contentType[0:9] == "text/html" {
				// this is probably a video website (like youtube)
				err = util.DownloadVideo(item.Link, filepath.Join(path, strconv.Itoa(int(item.ID))+".mp4"))
				ext = "mp4"
			}
		}
	}
	if err == nil {
		s.DB.UpdateCache(context.Background(), database.UpdateCacheParams{Extension: ext, ID: item.ID})
	} else {
		s.Log.Debug("error while caching link %s", item.Link)
	}
	return err
}
