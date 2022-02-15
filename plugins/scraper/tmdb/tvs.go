package tmdb

import (
	"encoding/json"
	"errors"
	"net/url"
	"strconv"
	"time"

	"github.com/Zogwine/Zogwine/internal/scraper/common"
)

func NewTVShowProvider() common.TVShowProvider {
	p := New()
	return &p
}

// tvs search
func (t *TMDB) SearchTVS(name string) ([]common.SearchData, error) {
	// retreive data with pagination
	data := TMDBTVSearch{}
	page := 1
	for {
		params := url.Values{}
		params.Add("query", name)
		raw, err := t.request("search/tv?"+params.Encode(), page)
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

func (t *TMDB) ListTVSTag() ([]common.TagData, error) {
	tags := []common.TagData{}

	raw, err := t.request("tv/"+t.ScraperID, 1)
	if err != nil {
		return tags, err
	}
	decode := TMDBTVShow{}
	err = json.Unmarshal(raw, &decode)
	if err != nil {
		return tags, err
	}

	for _, i := range decode.Genres {
		tags = append(tags, common.TagData{
			Name:  "genre",
			Value: i.Name,
		})
	}

	for _, i := range decode.OriginCountry {
		tags = append(tags, common.TagData{
			Name:  "country",
			Value: i,
		})
	}

	for _, i := range decode.Networks {
		tags = append(tags, common.TagData{
			Name:  "network",
			Value: i.Name,
			Icon:  t.ImageURL(i.LogoPath),
		})
	}

	for _, i := range decode.ProductionCompanies {
		tags = append(tags, common.TagData{
			Name:  "production",
			Value: i.Name,
			Icon:  t.ImageURL(i.LogoPath),
		})
	}

	return tags, nil
}

func (t *TMDB) ListTVSPerson() ([]common.PersonData, error) {
	pers := []common.PersonData{}

	raw, err := t.request("tv/"+t.ScraperID+"/credits", 1)
	if err != nil {
		return pers, err
	}
	decode := TMDBTVSCredits{}
	err = json.Unmarshal(raw, &decode)
	if err != nil {
		return pers, err
	}

	for _, i := range decode.Cast {
		pers = append(pers, common.PersonData{
			Name:        i.Name,
			Role:        i.KnownForDepartment,
			IsCharacter: false,
		})
	}

	for _, i := range decode.Crew {
		pers = append(pers, common.PersonData{
			Name:        i.Name,
			Role:        i.KnownForDepartment,
			IsCharacter: false,
		})
	}

	return pers, nil
}

func (t *TMDB) GetTVSUpcomingEpisode() (common.UpcomingData, error) {

	raw, err := t.request("tv/"+t.ScraperID, 1)
	if err != nil {
		return common.UpcomingData{}, err
	}
	decode := TMDBTVShow{}
	err = json.Unmarshal(raw, &decode)
	if err != nil {
		return common.UpcomingData{}, err
	}

	if decode.NextEpisodeToAir.Name == "" {
		return common.UpcomingData{}, errors.New("no data")
	}

	prem, _ := time.Parse("2006-01-02", decode.NextEpisodeToAir.AirDate)

	return common.UpcomingData{
		Title:     decode.NextEpisodeToAir.Name,
		Overview:  decode.NextEpisodeToAir.Overview,
		Icon:      t.ImageURL(decode.NextEpisodeToAir.StillPath),
		Premiered: prem.Unix(),
		ID1:       int64(decode.NextEpisodeToAir.SeasonNumber),
		ID2:       int64(decode.NextEpisodeToAir.EpisodeNumber),
		ScraperInfo: common.ScraperInfo{
			ScraperID:   strconv.Itoa(decode.NextEpisodeToAir.ID),
			ScraperName: t.ScraperName,
			ScraperData: "",
			ScraperLink: "",
		},
	}, nil
}
