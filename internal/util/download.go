package util

import (
	"fmt"
	"io"
	"net/http"
	"os"

	"github.com/Zogwine/Zogwine/pkg/goydl"
)

func DownloadFile(url string, filepath string) error {

	// Get the data
	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	// Create the file
	out, err := os.Create(filepath)
	if err != nil {
		return err
	}
	defer out.Close()

	// Write the body to file
	_, err = io.Copy(out, resp.Body)
	return err
}

func DownloadVideo(url string, path string) error {
	youtubeDl := goydl.NewYoutubeDl()
	youtubeDl.Options.Output.Value = path
	youtubeDl.Options.EmbedSubs.Value = true

	cmd, err := youtubeDl.Download(url)
	fmt.Println(err)

	go io.Copy(os.Stdout, youtubeDl.Stdout)
	go io.Copy(os.Stderr, youtubeDl.Stderr)

	if err != nil {
		return err
	}

	defer cmd.Wait()

	return nil
}
