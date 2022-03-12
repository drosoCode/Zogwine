package file

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"image"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/Zogwine/Zogwine/internal/database"
	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util"
	"github.com/corona10/goimagehash"
	"github.com/disintegration/gift"
	_ "golang.org/x/image/bmp"

	"github.com/Zogwine/Zogwine/pkg/ffprobe"
)

// package to analyze metadata (streams, aspect ratio, codecs, format, additional files) of a video file

type FileInfo struct {
	Format    string          `json:"format"`
	Duration  float64         `json:"duration"`
	Extension string          `json:"extension"`
	Video     json.RawMessage `json:"video"`
	Audio     json.RawMessage `json:"audio"`
	Subtitle  json.RawMessage `json:"subtitle"`
	Size      float64         `json:"size"`
}

type SubtitleStream struct {
	Index    int64  `json:"index"`
	Title    string `json:"title"`
	Language string `json:"language"`
	Codec    string `json:"codec"`
	File     string `json:"file"`
	Embedded bool   `json:"embedded"`
}

type AudioStream struct {
	Index    int64  `json:"index"`
	Codec    string `json:"codec"`
	Language string `json:"language"`
	Title    string `json:"title"`
	Channels int64  `json:"channels"`
}

type VideoStream struct {
	Index     int64   `json:"index"`
	Stereo3d  string  `json:"stereo3d"`
	Ratio     string  `json:"ratio"`
	Dimension string  `json:"dimension"`
	PixFmt    string  `json:"pixFmt"`
	Codec     string  `json:"codec"`
	Framerate float64 `json:"framerate"`
}

type VideoFileInfo struct {
	FileInfo
	Tmp        bool
	AddDate    int64
	UpdateDate int64
	Path       string
	IDLib      int64
	MediaType  database.MediaType
	MediaData  int64
}

// list potential subtitle files in the same folder and with the same starting name of a video file
func getSubtitleFilesList(videoFilePath string, supportedFiles []string) ([]SubtitleStream, error) {
	subtitles := make([]SubtitleStream, 0)

	fileName := filepath.Base(videoFilePath)
	fileName = strings.TrimSuffix(fileName, filepath.Ext(fileName)[1:])
	fileNameLen := len(fileName)

	dir := filepath.Dir(videoFilePath)

	files, err := os.ReadDir(dir)
	if err != nil {
		return subtitles, err
	}

	i := int64(0)
	for _, file := range files {
		if !file.Type().IsDir() {
			name := file.Name()
			ext := filepath.Ext(name)[1:]
			if util.Contains(supportedFiles, ext) && len(name) > fileNameLen && name[0:fileNameLen] == fileName {
				lang := name[fileNameLen:]
				lang = strings.ReplaceAll(lang[:len(lang)-len(ext)], ".", "")
				subtitles = append(subtitles, SubtitleStream{File: name, Title: "subfile", Language: lang, Codec: ext, Index: i, Embedded: false})
				i++
			}
		}
	}
	return subtitles, nil
}

// extract a specific frame from a video file
func ffmpegExtractFrame(videoFilePath string, stream int, frame int) (image.Image, string, error) {
	cmd := exec.Command("ffmpeg", "-hide_banner", "-loglevel", "error", "-i", videoFilePath, "-filter_complex", "[0:v:"+strconv.Itoa(stream)+"]select=gte(n\\,"+strconv.Itoa(frame)+")", "-vframes", "1", "-c:v", "bmp", "-f", "image2pipe", "-")

	var out bytes.Buffer
	cmd.Stderr = os.Stderr
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		log.Fatal(err)
	}

	return image.Decode(&out)
}

// test for SBS or TAB 3D on a specific image
func test3D(img image.Image, testSBS bool) bool {
	g1 := gift.New()
	g2 := gift.New()
	halfBound := img.Bounds()

	if testSBS {
		g1.Add(
			gift.CropToSize(img.Bounds().Max.X/2, img.Bounds().Max.Y, gift.LeftAnchor),
		)
		g2.Add(
			gift.CropToSize(img.Bounds().Max.X/2, img.Bounds().Max.Y, gift.RightAnchor),
		)
		halfBound.Max.X = halfBound.Max.X / 2
	} else {
		g1.Add(
			gift.CropToSize(img.Bounds().Max.X, img.Bounds().Max.Y/2, gift.TopAnchor),
		)
		g2.Add(
			gift.CropToSize(img.Bounds().Max.X, img.Bounds().Max.Y/2, gift.BottomAnchor),
		)
		halfBound.Max.Y = halfBound.Max.Y / 2
	}

	dst1 := image.NewRGBA(g1.Bounds(halfBound))
	dst2 := image.NewRGBA(g2.Bounds(halfBound))
	g1.Draw(dst1, img)
	g2.Draw(dst2, img)

	hash1, _ := goimagehash.AverageHash(dst1)
	hash2, _ := goimagehash.AverageHash(dst2)
	distance, _ := hash1.Distance(hash2)

	return distance < 5
}

// detect the 3D type of a video file (NONE, SBS or TAB)
func detect3DMode(videoFilePath string, stream int, duration float64) string {
	f1 := 10
	f2 := 1000

	if f1 > int(duration) {
		f1 = 0
	}
	if f2 > int(duration) {
		f2 = int(duration)
	}

	frame1, _, err := ffmpegExtractFrame(videoFilePath, stream, f1)
	if err != nil {
		return "NONE"
	}
	frame2, _, err := ffmpegExtractFrame(videoFilePath, stream, f2)
	if err != nil {
		return "NONE"
	}

	if test3D(frame1, true) && test3D(frame2, true) {
		return "SBS"
	} else if test3D(frame1, false) && test3D(frame2, false) {
		return "TAB"
	} else {
		return "NONE"
	}
}

// gather info on a video file
func getFileInfos(videoFilePath string, supportedVideo []string, supportedSubtitles []string, skip3d bool) (FileInfo, error) {
	extension := filepath.Ext(videoFilePath)[1:]

	if !util.Contains(supportedVideo, extension) {
		return FileInfo{}, errors.New("video file not supported")
	}

	data, err := ffprobe.ProbeURL(context.Background(), videoFilePath)
	if err != nil {
		return FileInfo{}, err
	}

	videoStreams := make([]VideoStream, 0)
	for i, stream := range data.StreamType(ffprobe.StreamVideo) {
		fr := strings.Split(stream.AvgFrameRate, "/")
		framerate := 0.0
		if len(fr) >= 2 {
			fr1, _ := strconv.ParseFloat(fr[0], 64)
			fr2, _ := strconv.ParseFloat(fr[1], 64)
			framerate = fr1 / fr2
		}
		stereo3d := "NONE"
		if !skip3d {
			stereo3d = detect3DMode(videoFilePath, i, data.Format.DurationSeconds)
		}
		videoStreams = append(videoStreams, VideoStream{
			Ratio:     stream.DisplayAspectRatio,
			Dimension: strconv.Itoa(stream.Width) + "x" + strconv.Itoa(stream.Height),
			PixFmt:    stream.PixFmt,
			Codec:     stream.CodecName,
			Stereo3d:  stereo3d,
			Framerate: framerate,
			Index:     int64(stream.Index),
		})
	}
	videoStreamsJson, _ := json.Marshal(videoStreams)

	audioStreams := make([]AudioStream, 0)
	for _, stream := range data.StreamType(ffprobe.StreamAudio) {
		audioStreams = append(audioStreams, AudioStream{
			Codec:    stream.CodecName,
			Index:    int64(stream.Index),
			Language: stream.Tags.Language,
			Title:    stream.Tags.Title,
			Channels: int64(stream.Channels),
		})
	}
	audioStreamsJson, _ := json.Marshal(audioStreams)

	subtitleStreams, _ := getSubtitleFilesList(videoFilePath, supportedSubtitles)
	for _, stream := range data.StreamType(ffprobe.StreamSubtitle) {
		subtitleStreams = append(subtitleStreams, SubtitleStream{
			Codec:    stream.CodecName,
			Index:    int64(stream.Index),
			Language: stream.Tags.Language,
			Title:    stream.Tags.Title,
			Embedded: true,
			File:     "",
		})
	}
	subtitleStreamsJson, _ := json.Marshal(subtitleStreams)

	size, _ := strconv.ParseFloat(data.Format.Size, 64)

	ret := FileInfo{
		Format:    data.Format.FormatName,
		Duration:  data.Format.DurationSeconds,
		Extension: extension,
		Size:      size,
		Video:     videoStreamsJson,
		Audio:     audioStreamsJson,
		Subtitle:  subtitleStreamsJson,
	}

	return ret, nil
}

// Create a new video_file entry for a specific media and returns the id of the entry
// You need to provide the library id (idlib) and the path to the file in this library (videoFilePath) to analyse the video
// mediaType, mediaData must be provided to link the video file to the correct media entity
// tmp describes if the video file is temporary or not
func AddVideoFile(s *status.Status, idlib int64, videoFilePath string, mediaType database.MediaType, mediaData int64, tmp bool) (int64, error) {
	ctx := context.Background()
	lib, err := s.DB.GetLibrary(ctx, idlib)
	if err != nil {
		return 0, err
	}
	path := filepath.Join(lib.Path, videoFilePath)

	info, err := getFileInfos(path, s.Config.Files.Video, s.Config.Files.Subtitle, s.Config.Analyzer.Video.Skip3D)
	if err != nil {
		return 0, err
	}

	id, err := s.DB.AddVideoFile(ctx, database.AddVideoFileParams{
		IDLib:      idlib,
		MediaType:  mediaType,
		MediaData:  mediaData,
		Format:     info.Format,
		Duration:   info.Duration,
		Extension:  info.Extension,
		Video:      info.Video,
		Audio:      info.Audio,
		Subtitle:   info.Subtitle,
		Size:       info.Size,
		Path:       videoFilePath,
		Tmp:        tmp,
		AddDate:    time.Now().Unix(),
		UpdateDate: time.Now().Unix(),
	})
	if err != nil {
		return 0, err
	}

	return id, nil
}

func UpdateVideoFile(s *status.Status, idlib int64, videoFilePath string) error {
	ctx := context.Background()
	lib, err := s.DB.GetLibrary(ctx, idlib)
	if err != nil {
		return err
	}
	path := filepath.Join(lib.Path, videoFilePath)

	info, err := getFileInfos(path, s.Config.Files.Video, s.Config.Files.Subtitle, s.Config.Analyzer.Video.Skip3D)
	if err != nil {
		return err
	}

	data, err := s.DB.GetVideoFileFromPath(ctx, database.GetVideoFileFromPathParams{IDLib: idlib, Path: videoFilePath})
	if err != nil {
		return err
	}

	s.DB.UpdateVideoFile(ctx, database.UpdateVideoFileParams{
		Format:     info.Format,
		Duration:   info.Duration,
		Extension:  info.Extension,
		Video:      info.Video,
		Audio:      info.Audio,
		Subtitle:   info.Subtitle,
		Size:       info.Size,
		UpdateDate: time.Now().Unix(),
		ID:         data.ID,
	})
	if err != nil {
		return err
	}

	return nil
}

func parseSQLResponse(data database.VideoFile) VideoFileInfo {
	v := VideoFileInfo{
		IDLib:      data.IDLib,
		MediaType:  data.MediaType,
		MediaData:  data.MediaData,
		Path:       data.Path,
		Tmp:        data.Tmp,
		AddDate:    data.AddDate,
		UpdateDate: data.UpdateDate,
	}
	v.Format = data.Format
	v.Duration = data.Duration
	v.Extension = data.Extension
	v.Size = data.Size
	json.Unmarshal(data.Video, &v.Video)
	json.Unmarshal(data.Audio, &v.Audio)
	json.Unmarshal(data.Subtitle, &v.Subtitle)
	return v
}

func GetFileInfo(s *status.Status, idvid int64) (VideoFileInfo, error) {
	data, err := s.DB.GetVideoFile(context.Background(), idvid)
	if err != nil {
		return VideoFileInfo{}, err
	}
	return parseSQLResponse(data), nil
}

func GetFileInfoFromPath(s *status.Status, idlib int64, path string) (VideoFileInfo, error) {
	data, err := s.DB.GetVideoFileFromPath(context.Background(), database.GetVideoFileFromPathParams{IDLib: idlib, Path: path})
	if err != nil {
		return VideoFileInfo{}, err
	}
	return parseSQLResponse(data), nil
}

func ListFileInfoFromMedia(s *status.Status, mediaType database.MediaType, mediaData int64) ([]VideoFileInfo, error) {
	data, err := s.DB.ListVideoFileFromMedia(context.Background(), database.ListVideoFileFromMediaParams{MediaType: mediaType, MediaData: mediaData})
	ret := make([]VideoFileInfo, 0)
	if err != nil {
		return ret, err
	}
	for _, item := range data {
		ret = append(ret, parseSQLResponse(item))
	}
	return ret, nil
}
