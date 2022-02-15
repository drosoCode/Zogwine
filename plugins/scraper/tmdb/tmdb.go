package tmdb

import (
	"errors"
	"io/ioutil"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	log "github.com/sirupsen/logrus"
)

type TMDB struct {
	APIKey      string
	Language    string
	ScraperName string
	ScraperID   string
	ScraperData string
	Logger      *log.Logger
}

func New() TMDB {
	return TMDB{ScraperName: "tmdb", Language: "en-US", Logger: nil, ScraperID: "", ScraperData: ""}
}

// configure the provider's settings
func (t *TMDB) Setup(config map[string]string, logger *log.Logger) error {
	t.Logger = logger
	if val, ok := config["api_key"]; ok {
		t.APIKey = val
	} else {
		return errors.New("empty api key")
	}
	if val, ok := config["language"]; ok {
		t.Language = val
	}
	return nil
}

func (p *TMDB) Configure(ScraperID string, ScraperData string) {
	p.ScraperID = ScraperID
	p.ScraperData = ScraperData
}

/*
func NewMovieProvider(logger *log.Logger) common.MovieProvider {
	p := New(logger)
	return &p
}

func NewPersonProvider(logger *log.Logger) common.PersonProvider {
	p := New(logger)
	return &p
}*/

// helper to make a request to the api
func (t *TMDB) request(link string, page int) ([]byte, error) {
	errFields := log.Fields{
		"file":     "tmdb",
		"function": "request",
		"code":     false,
	}

	if link == "" {
		t.Logger.WithFields(errFields).Error("empty url")
		return nil, errors.New("empty url")
	}
	if t.APIKey == "" {
		t.Logger.WithFields(errFields).Error("empty api key")
		return nil, errors.New("empty api key")
	}

	param := "?"
	m, _ := url.ParseQuery(link)
	for _, v := range m {
		if len(v) > 0 && v[0] != "" {
			param = "&"
		}
	}

	u := "https://api.themoviedb.org/3/" + link + param + "api_key=" + t.APIKey + "&page=" + strconv.Itoa(page) + "&language=" + t.Language
	resp, err := http.Get(u)

	if err != nil || resp.StatusCode != 200 {
		t.Logger.WithFields(errFields).Infof("requested url: %s", u)
		t.Logger.WithFields(errFields).Errorf("request error: %v - status code: %d", err, resp.StatusCode)
		return nil, err
	}

	data, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		t.Logger.WithFields(errFields).Errorf("request read error: %v", err)
		return nil, err
	}

	return data, nil
}

func (t *TMDB) ImageURL(id string) string {
	if id == "" {
		return ""
	}
	return "https://image.tmdb.org/t/p/w500/" + id
}

func (t *TMDB) MediaLink(tp int, id1 string, id2 string, id3 string) string {
	if id1 == "" {
		return ""
	}
	if tp == 0 {
		return "https://www.themoviedb.org/tv/" + id1
	} else if tp == 1 {
		if id2 == "" {
			return ""
		}
		return "https://www.themoviedb.org/tv/" + id1 + "/season/" + id2
	} else if tp == 2 {
		if id2 == "" || id3 == "" {
			return ""
		}
		return "https://www.themoviedb.org/tv/" + id1 + "/season/" + id2 + "/episode/" + id3
	} else if tp == 3 {
		return "https://www.themoviedb.org/movie/" + id1
	} else if tp == 4 {
		return "https://www.themoviedb.org/person/" + id1
	}
	return ""
}

// trailer

func (t *TMDB) getTrailerFromVideo(data TMDBVideo) string {
	layout := "2006-01-02T15:04:05.000Z"

	type kv map[string]string
	trailers := make([]kv, 4)

	// sort videos in 4 categories, Official Trailers, Official Videos, Unofficial Trailer, Unofficial Videos
	for _, item := range data.Results {
		link := "https://www.youtube.com/watch?v=" + item.Key
		if item.Site == "YouTube" {
			if item.Official {
				if strings.Contains(strings.ToLower(item.Name), "trailer") {
					trailers[0][item.PublishedAt] = link
				} else {
					trailers[1][item.PublishedAt] = link
				}
			} else {
				if strings.Contains(strings.ToLower(item.Name), "trailer") {
					trailers[2][item.PublishedAt] = link
				} else {
					trailers[3][item.PublishedAt] = link
				}
			}
		}
	}

	// return the oldest date from the first non empty category
	// ideally this would return the first official trailer for a given media
	for _, tr := range trailers {
		dt := ""
		for k := range tr {
			if dt == "" {
				dt = k
			} else {
				t1, _ := time.Parse(layout, k)
				t2, _ := time.Parse(layout, dt)
				if t1.Unix() < t2.Unix() {
					dt = k
				}
			}
			if dt != "" {
				return tr[dt]
			}
		}
	}
	return ""
}

type TMDBVideo struct {
	ID      int `json:"id"`
	Results []struct {
		ISO6391     string `json:"iso_639_1"`
		ISO31661    string `json:"iso_3166_1"`
		Name        string `json:"name"`
		Key         string `json:"string"`
		Site        string `json:"site"`
		Size        int    `json:"size"`
		Type        string `json:"type"`
		Official    bool   `json:"official"`
		PublishedAt string `json:"published_at"`
		ID          string `json:"id"`
	} `json:"results"`
}
