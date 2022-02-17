package tmdb

import (
	"encoding/json"
	"strconv"
	"time"

	"github.com/Zogwine/Zogwine/internal/scraper/common"
)

func NewPersonProvider() common.PersonProvider {
	p := New()
	return &p
}

func (t *TMDB) SearchPerson(name string) ([]common.SearchData, error) {
	ret := make([]common.SearchData, 0)

	raw, err := t.request("movie/"+t.ScraperID, 1)
	if err != nil {
		return ret, err
	}
	decode := TMDBPersonSearch{}
	err = json.Unmarshal(raw, &decode)
	if err != nil {
		return ret, err
	}

	for _, item := range decode.Results {
		ret = append(ret, common.SearchData{
			Title:     item.Name,
			Overview:  "",
			Icon:      t.ImageURL(item.ProfilePath),
			Premiered: 0,
			ScraperInfo: common.ScraperInfo{
				ScraperID:   strconv.Itoa(item.ID),
				ScraperName: t.ScraperName,
				ScraperData: "",
				ScraperLink: t.MediaLink(5, strconv.Itoa(item.ID), "", ""),
			},
		})
	}

	return ret, nil
}

func (t *TMDB) GetPerson() (common.PersonDetails, error) {
	raw, err := t.request("person/"+t.ScraperID, 1)
	if err != nil {
		return common.PersonDetails{}, err
	}
	decode := TMDBPersonData{}
	err = json.Unmarshal(raw, &decode)
	if err != nil {
		return common.PersonDetails{}, err
	}

	birth, _ := time.Parse("2006-01-02", decode.Birthday)
	deathdate := int64(0)
	death, err := time.Parse("2006-01-02", decode.Deathday)
	if err == nil {
		deathdate = death.Unix()
	}
	return common.PersonDetails{
		Name:        decode.Name,
		Birthdate:   birth.Unix(),
		Deathdate:   deathdate,
		Gender:      int64(decode.Gender),
		Description: decode.Biography,
		Icon:        t.ImageURL(decode.ProfilePath),
		Rating:      int64(decode.Popularity),
		KnownFor:    decode.KnownForDepartment,
		ScraperInfo: common.ScraperInfo{
			ScraperID:   t.ScraperID,
			ScraperName: t.ScraperName,
			ScraperData: "",
			ScraperLink: t.MediaLink(5, t.ScraperID, "", ""),
		},
	}, nil
}
