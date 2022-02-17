package tmdb

import (
	"encoding/json"
	"errors"
	"net/url"
	"strconv"
	"time"

	"github.com/Zogwine/Zogwine/internal/scraper/common"
)

func NewMovieProvider() common.MovieProvider {
	p := New()
	return &p
}

// mov search
func (t *TMDB) SearchMovie(name string, year int) ([]common.SearchData, error) {
	// retreive data with pagination
	data := TMDBMovieSearch{}
	page := 1
	for {
		params := url.Values{}
		params.Add("query", name)
		if year != 0 {
			params.Add("year", strconv.Itoa(year))
		}
		raw, err := t.request("search/movie?"+params.Encode(), page)
		if err != nil {
			return nil, err
		}
		decode := TMDBMovieSearch{}
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
		prem, _ := time.Parse("2006-01-02", item.ReleaseDate)
		sd := common.SearchData{
			Title:     item.Title,
			Overview:  item.Overview,
			Icon:      t.ImageURL(item.PosterPath),
			Premiered: prem.Unix(),
			ScraperInfo: common.ScraperInfo{
				ScraperName: t.ScraperName,
				ScraperID:   strconv.Itoa(item.ID),
				ScraperData: "",
				ScraperLink: t.MediaLink(3, strconv.Itoa(item.ID), "", ""),
			},
		}
		ret = append(ret, sd)
	}

	return ret, nil
}

// get movie data
func (t *TMDB) GetMovie() (common.MovieData, error) {
	// get movie details
	raw, err := t.request("movie/"+t.ScraperID, 1)
	if err != nil {
		return common.MovieData{}, err
	}
	decode := TMDBMovie{}
	err = json.Unmarshal(raw, &decode)
	if err != nil {
		return common.MovieData{}, err
	}

	// get associated videos (to extract trailer)
	raw, err = t.request("movie/"+t.ScraperID+"/videos", 1)
	if err != nil {
		return common.MovieData{}, err
	}
	vid := TMDBVideo{}
	err = json.Unmarshal(raw, &vid)
	if err != nil {
		return common.MovieData{}, err
	}

	prem, _ := time.Parse("2006-01-02", decode.ReleaseDate)
	return common.MovieData{
		Title:      decode.Title,
		Overview:   decode.Overview,
		Icon:       t.ImageURL(decode.PosterPath),
		Fanart:     t.ImageURL(decode.BackdropPath),
		Website:    decode.Homepage,
		Trailer:    t.getTrailerFromVideo(vid),
		Premiered:  prem.Unix(),
		Rating:     int64(decode.VoteAverage),
		Collection: int64(decode.BelongsToCollection.ID),
		ScraperInfo: common.ScraperInfo{
			ScraperID:   t.ScraperID,
			ScraperName: t.ScraperName,
			ScraperData: t.ScraperData,
			ScraperLink: t.MediaLink(0, t.ScraperID, "", ""),
		},
	}, nil
}

// get movie collection data
func (t *TMDB) GetMovieCollection() (common.MovieCollectionData, error) {
	// get movie details
	raw, err := t.request("collection/"+t.ScraperID, 1)
	if err != nil {
		return common.MovieCollectionData{}, err
	}
	decode := TMDBMovieCollection{}
	err = json.Unmarshal(raw, &decode)
	if err != nil {
		return common.MovieCollectionData{}, err
	}
	prem, _ := time.Parse("2006-01-02", decode.Parts[0].ReleaseDate)

	return common.MovieCollectionData{
		Title:     decode.Name,
		Overview:  decode.Overview,
		Icon:      t.ImageURL(decode.PosterPath),
		Fanart:    t.ImageURL(decode.BackdropPath),
		Premiered: prem.Unix(),
		Rating:    int64(decode.Parts[0].VoteAverage),
		ScraperInfo: common.ScraperInfo{
			ScraperID:   t.ScraperID,
			ScraperName: t.ScraperName,
			ScraperData: "",
			ScraperLink: t.MediaLink(4, t.ScraperID, "", ""),
		},
	}, nil
}

func (t *TMDB) ListMoviePerson() ([]common.PersonData, error) {
	pers := []common.PersonData{}

	raw, err := t.request("movie/"+t.ScraperID+"/credits", 1)
	if err != nil {
		return pers, err
	}
	decode := TMDBMovieCredits{}
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

func (t *TMDB) ListMovieTag() ([]common.TagData, error) {
	tags := []common.TagData{}

	raw, err := t.request("movie/"+t.ScraperID, 1)
	if err != nil {
		return tags, err
	}
	decode := TMDBMovie{}
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

	for _, i := range decode.ProductionCompanies {
		tags = append(tags, common.TagData{
			Name:  "production",
			Value: i.Name,
			Icon:  t.ImageURL(i.LogoPath),
		})
	}

	return tags, nil
}

func (t *TMDB) GetMovieUpcoming() (common.UpcomingData, error) {
	return common.UpcomingData{}, errors.New("no data")
}
