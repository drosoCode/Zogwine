package tmdb

import (
	"encoding/json"
	"errors"
	"io/ioutil"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"github.com/Zogwine/Zogwine/internal/scraper/common"
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

func NewTVShowProvider() common.TVShowProvider {
	p := New()
	return &p
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

// tvs search

func (t *TMDB) SearchTVS(name string) ([]common.SearchData, error) {
	// retreive data with pagination
	data := TMDBTVSearch{}
	page := 1
	for {
		raw, err := t.request("search/tv?query="+name, page)
		if err != nil {
			return nil, err
		}
		decode := TMDBTVSearch{}
		err = json.Unmarshal(raw, &decode)
		if err != nil {
			return nil, err
		}
		data.Results = append(data.Results, decode.Results...)
		if decode.Page < decode.TotalPages {
			page++
		} else {
			break
		}
	}

	// process data
	ret := make([]common.SearchData, 0)
	for _, item := range data.Results {
		prem, _ := time.Parse("2006-01-02", item.FirstAirDate)
		sd := common.SearchData{
			Title:     item.Name,
			Overview:  item.Overview,
			Icon:      t.ImageURL(item.PosterPath),
			Premiered: prem.Unix(),
			ScraperInfo: common.ScraperInfo{
				ScraperName: t.ScraperName,
				ScraperID:   strconv.Itoa(item.ID),
				ScraperData: "",
				ScraperLink: t.MediaLink(0, strconv.Itoa(item.ID), "", ""),
			},
		}
		ret = append(ret, sd)

		// add episode groups for each result
		raw, err := t.request("tv/"+strconv.Itoa(item.ID)+"/episode_groups", 1)
		if err == nil {
			decode := TMDBEpisodeGroup{}
			err = json.Unmarshal(raw, &decode)
			if err == nil {
				for _, d := range decode.Results {
					// make a copy of the original result and edit the fields relative to the episode group
					eg := sd
					eg.Title = d.Name
					eg.Overview = d.Description
					eg.ScraperData = d.ID
					ret = append(ret, eg)
				}
			}
		}
	}

	return ret, nil
}

// tvs get show
func (t *TMDB) GetTVS() (common.TVSData, error) {
	// get tvs details
	raw, err := t.request("tv/"+t.ScraperID, 1)
	if err != nil {
		return common.TVSData{}, err
	}
	decode := TMDBTVShow{}
	err = json.Unmarshal(raw, &decode)
	if err != nil {
		return common.TVSData{}, err
	}

	// get associated videos (to extract trailer)
	raw, err = t.request("tv/"+t.ScraperID, 1)
	if err != nil {
		return common.TVSData{}, err
	}
	vid := TMDBVideo{}
	err = json.Unmarshal(raw, &vid)
	if err != nil {
		return common.TVSData{}, err
	}

	prem, _ := time.Parse("2006-01-02", decode.FirstAirDate)
	return common.TVSData{
		Title:     decode.Name,
		Overview:  decode.Overview,
		Icon:      t.ImageURL(decode.PosterPath),
		Fanart:    t.ImageURL(decode.BackdropPath),
		Website:   decode.Homepage,
		Trailer:   t.getTrailerFromVideo(vid),
		Premiered: prem.Unix(),
		Rating:    int64(decode.VoteAverage),
		ScraperInfo: common.ScraperInfo{
			ScraperID:   t.ScraperID,
			ScraperName: t.ScraperName,
			ScraperData: t.ScraperData,
			ScraperLink: t.MediaLink(0, t.ScraperID, "", ""),
		},
	}, nil
}

func (t *TMDB) GetTVSSeason(season int) (common.TVSSeasonData, error) {
	raw, err := t.request("tv/"+t.ScraperID+"/season/"+strconv.Itoa(season), 1)
	if err != nil {
		return common.TVSSeasonData{}, err
	}
	decode := TMDBSeason{}
	err = json.Unmarshal(raw, &decode)
	if err != nil {
		return common.TVSSeasonData{}, err
	}

	prem, _ := time.Parse("2006-01-02", decode.Episodes[0].AirDate)

	vote := 0.0
	for _, i := range decode.Episodes {
		vote += i.VoteAverage
	}
	vote /= float64(len(decode.Episodes))

	return common.TVSSeasonData{
		Title:     decode.Name,
		Overview:  decode.Overview,
		Icon:      t.ImageURL(decode.PosterPath),
		Fanart:    "",
		Trailer:   "",
		Premiered: prem.Unix(),
		Rating:    int64(vote),
		ScraperInfo: common.ScraperInfo{
			ScraperName: t.ScraperName,
			ScraperID:   t.ScraperID,
			ScraperData: t.ScraperData,
			ScraperLink: t.MediaLink(1, t.ScraperID, strconv.Itoa(season), ""),
		},
	}, nil
}

// get tvs episode
func (t *TMDB) GetTVSEpisode(season int, episode int) (common.TVSEpisodeData, error) {
	var decode TMDBEpisode

	if t.ScraperData == "" {
		raw, err := t.request("tv/"+t.ScraperID+"/season/"+strconv.Itoa(season)+"/episode/"+strconv.Itoa(episode), 1)
		if err != nil {
			return common.TVSEpisodeData{}, err
		}
		decode = TMDBEpisode{}
		err = json.Unmarshal(raw, &decode)
		if err != nil {
			return common.TVSEpisodeData{}, err
		}
	} else {
		raw, err := t.request("tv/episode_group/"+t.ScraperData, 1)
		if err != nil {
			return common.TVSEpisodeData{}, err
		}
		dec := TMDBEpisodeGroupData{}
		err = json.Unmarshal(raw, &dec)
		if err != nil {
			return common.TVSEpisodeData{}, err
		}

		if len(dec.Groups) == 0 {
			return common.TVSEpisodeData{}, errors.New("no data")
		}
		for _, i := range dec.Groups[0].Episodes {
			if i.SeasonNumber == season && i.EpisodeNumber == episode {
				decode = i
			}
		}
	}

	if decode.Name == "" {
		return common.TVSEpisodeData{}, errors.New("no data")
	}

	prem, _ := time.Parse("2006-01-02", decode.AirDate)

	return common.TVSEpisodeData{
		Title:     decode.Name,
		Overview:  decode.Overview,
		Icon:      t.ImageURL(decode.StillPath),
		Premiered: prem.Unix(),
		Rating:    int64(decode.VoteAverage),
		ScraperInfo: common.ScraperInfo{
			ScraperName: t.ScraperName,
			ScraperID:   t.ScraperID,
			ScraperData: t.ScraperData,
			ScraperLink: t.MediaLink(2, t.ScraperID, strconv.Itoa(season), strconv.Itoa(episode)),
		},
	}, nil
}
