package file

import (
	"context"
	"errors"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/Zogwine/Zogwine/internal/database"
	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util"
)

func GetMediaPath(s *status.Status, mediaType database.MediaType, mediaData int64, selector int64) (string, error) {
	ctx := context.Background()
	data, err := s.DB.GetVideoFileFromMedia(ctx, database.GetVideoFileFromMediaParams{MediaType: mediaType, MediaData: mediaData, Offset: int32(selector)})
	if err != nil {
		return "", err
	}
	lib, err := s.DB.GetLibrary(ctx, data.IDLib)
	if err != nil {
		return "", err
	}
	return filepath.Join(lib.Path, data.Path), nil
}

func GetMediaFromUrl(s *status.Status, url string) (database.MediaType, int64, error) {
	// http://base.url/out/transcodeid/streamXXX.ts
	baseOut := s.Config.Server.BaseURL + "/out/"
	if pos := strings.Index(url, baseOut); pos > -1 {
		pos += len(baseOut)
		tid := url[pos:]
		if end := strings.Index(tid, "/"); end > -1 {
			tid = tid[:end]
		}

		if task, ok := s.ListTranscodeTask()[tid]; ok {
			return task.MediaType, task.MediaData, nil
		}
	}

	// http://base.url/content/mediatype/mediadata/selector?/file?
	baseContent := s.Config.Server.BaseURL + "/content/"
	if pos := strings.Index(url, baseContent); pos > -1 {
		data := strings.Split(url[pos+len(baseContent):], "/")
		if len(data) >= 2 {
			mediaData, _ := strconv.ParseInt(data[1], 10, 64)
			return database.MediaType(data[0]), mediaData, nil
		}
	}

	return "", 0, errors.New("not found")
}

func IsVideo(s *status.Status, path string) bool {
	return util.Contains(s.Config.Files.Video, filepath.Ext(path)[1:])
}
