// Code generated by sqlc. DO NOT EDIT.

package database

import (
	"encoding/json"
	"fmt"
)

type MediaType string

const (
	MediaTypeUnknonwn        MediaType = "unknonwn"
	MediaTypeTvsEpisode      MediaType = "tvs_episode"
	MediaTypeTvs             MediaType = "tvs"
	MediaTypeMovie           MediaType = "movie"
	MediaTypeUrl             MediaType = "url"
	MediaTypeTvsSeason       MediaType = "tvs_season"
	MediaTypeMovieCollection MediaType = "movie_collection"
	MediaTypePerson          MediaType = "person"
)

func (e *MediaType) Scan(src interface{}) error {
	switch s := src.(type) {
	case []byte:
		*e = MediaType(s)
	case string:
		*e = MediaType(s)
	default:
		return fmt.Errorf("unsupported scan type for MediaType: %T", src)
	}
	return nil
}

type Cache struct {
	ID        int64  `json:"id"`
	Link      string `json:"link"`
	Extension string `json:"extension"`
	Cached    bool   `json:"cached"`
}

type Credential struct {
	ID         int64  `json:"id"`
	Username   string `json:"username"`
	Password   string `json:"password"`
	Address    string `json:"address"`
	Port       int64  `json:"port"`
	Data       string `json:"data"`
	AddDate    int64  `json:"addDate"`
	UpdateDate int64  `json:"updateDate"`
}

type Device struct {
	ID           int64  `json:"id"`
	Name         string `json:"name"`
	Type         string `json:"type"`
	IDCredential int64  `json:"idCredential"`
	Enabled      bool   `json:"enabled"`
}

type Episode struct {
	ID          int64  `json:"id"`
	Title       string `json:"title"`
	Overview    string `json:"overview"`
	Icon        string `json:"icon"`
	Premiered   int64  `json:"premiered"`
	Season      int64  `json:"season"`
	Episode     int64  `json:"episode"`
	Rating      int64  `json:"rating"`
	ScraperName string `json:"scraperName"`
	ScraperData string `json:"scraperData"`
	ScraperLink string `json:"scraperLink"`
	ScraperID   string `json:"scraperID"`
	IDShow      int64  `json:"idShow"`
	AddDate     int64  `json:"addDate"`
	UpdateDate  int64  `json:"updateDate"`
	UpdateMode  int64  `json:"updateMode"`
}

type Filler struct {
	ID          int64     `json:"id"`
	ScraperName string    `json:"scraperName"`
	ScraperID   string    `json:"scraperID"`
	ScraperData string    `json:"scraperData"`
	ScraperLink string    `json:"scraperLink"`
	AddDate     int64     `json:"addDate"`
	UpdateDate  int64     `json:"updateDate"`
	UpdateMode  int64     `json:"updateMode"`
	MediaType   MediaType `json:"mediaType"`
	MediaData   int64     `json:"mediaData"`
}

type FillerLink struct {
	IDFiller  int64     `json:"idFiller"`
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
	Value     int64     `json:"value"`
}

type Group struct {
	ID      int64  `json:"id"`
	Name    string `json:"name"`
	Enabled bool   `json:"enabled"`
	System  bool   `json:"system"`
}

type GroupLink struct {
	IDGroup int64 `json:"idGroup"`
	IDUser  int64 `json:"idUser"`
}

type Library struct {
	ID        int64     `json:"id"`
	Name      string    `json:"name"`
	Path      string    `json:"path"`
	MediaType MediaType `json:"mediaType"`
}

type Movie struct {
	ID           int64  `json:"id"`
	Title        string `json:"title"`
	Overview     string `json:"overview"`
	Icon         string `json:"icon"`
	Fanart       string `json:"fanart"`
	Premiered    int64  `json:"premiered"`
	Rating       int64  `json:"rating"`
	Trailer      string `json:"trailer"`
	Website      string `json:"website"`
	IDCollection int64  `json:"idCollection"`
	ScraperName  string `json:"scraperName"`
	ScraperID    string `json:"scraperID"`
	ScraperData  string `json:"scraperData"`
	ScraperLink  string `json:"scraperLink"`
	AddDate      int64  `json:"addDate"`
	UpdateDate   int64  `json:"updateDate"`
	UpdateMode   int64  `json:"updateMode"`
}

type MovieCollection struct {
	ID          int64  `json:"id"`
	Title       string `json:"title"`
	Overview    string `json:"overview"`
	Premiered   int64  `json:"premiered"`
	Icon        string `json:"icon"`
	Fanart      string `json:"fanart"`
	Rating      int64  `json:"rating"`
	ScraperName string `json:"scraperName"`
	ScraperID   string `json:"scraperID"`
	ScraperData string `json:"scraperData"`
	ScraperLink string `json:"scraperLink"`
	AddDate     int64  `json:"addDate"`
	UpdateDate  int64  `json:"updateDate"`
	UpdateMode  int64  `json:"updateMode"`
}

type Person struct {
	ID          int64  `json:"id"`
	Name        string `json:"name"`
	Gender      int64  `json:"gender"`
	Birth       int64  `json:"birth"`
	Death       int64  `json:"death"`
	Overview    string `json:"overview"`
	Icon        string `json:"icon"`
	KnownFor    string `json:"knownFor"`
	Rating      int64  `json:"rating"`
	ScraperName string `json:"scraperName"`
	ScraperID   string `json:"scraperID"`
	ScraperData string `json:"scraperData"`
	ScraperLink string `json:"scraperLink"`
	AddDate     int64  `json:"addDate"`
	UpdateDate  int64  `json:"updateDate"`
	UpdateMode  int64  `json:"updateMode"`
}

type PersonLink struct {
	IDPerson  int64     `json:"idPerson"`
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
	IDRole    int64     `json:"idRole"`
}

type Role struct {
	ID          int64  `json:"id"`
	Name        string `json:"name"`
	Overview    string `json:"overview"`
	Icon        string `json:"icon"`
	ScraperName string `json:"scraperName"`
	ScraperID   string `json:"scraperID"`
	ScraperData string `json:"scraperData"`
	ScraperLink string `json:"scraperLink"`
	AddDate     int64  `json:"addDate"`
	UpdateDate  int64  `json:"updateDate"`
	UpdateMode  int64  `json:"updateMode"`
}

type Scraper struct {
	Provider  string          `json:"provider"`
	Priority  int64           `json:"priority"`
	MediaType []MediaType     `json:"mediaType"`
	Settings  json.RawMessage `json:"settings"`
	Enabled   bool            `json:"enabled"`
}

type Season struct {
	IDShow      int64  `json:"idShow"`
	Season      int64  `json:"season"`
	Title       string `json:"title"`
	Overview    string `json:"overview"`
	Icon        string `json:"icon"`
	Fanart      string `json:"fanart"`
	Premiered   int64  `json:"premiered"`
	Rating      int64  `json:"rating"`
	Trailer     string `json:"trailer"`
	ScraperName string `json:"scraperName"`
	ScraperID   string `json:"scraperID"`
	ScraperData string `json:"scraperData"`
	ScraperLink string `json:"scraperLink"`
	AddDate     int64  `json:"addDate"`
	UpdateDate  int64  `json:"updateDate"`
	UpdateMode  int64  `json:"updateMode"`
}

type Selection struct {
	MediaType MediaType       `json:"mediaType"`
	MediaData int64           `json:"mediaData"`
	Data      json.RawMessage `json:"data"`
}

type Status struct {
	IDUser     int64     `json:"idUser"`
	MediaType  MediaType `json:"mediaType"`
	MediaData  int64     `json:"mediaData"`
	WatchCount int64     `json:"watchCount"`
	WatchTime  float64   `json:"watchTime"`
	LastDate   int64     `json:"lastDate"`
}

type Tag struct {
	ID    int64  `json:"id"`
	Name  string `json:"name"`
	Value string `json:"value"`
	Icon  string `json:"icon"`
}

type TagLink struct {
	IDTag     int64     `json:"idTag"`
	MediaType MediaType `json:"mediaType"`
	MediaData int64     `json:"mediaData"`
}

type Tracker struct {
	ID           int64  `json:"id"`
	IDUser       int64  `json:"idUser"`
	Name         string `json:"name"`
	Type         string `json:"type"`
	IDCredential int64  `json:"idCredential"`
	Direction    int64  `json:"direction"`
	SyncTypes    string `json:"syncTypes"`
	Enabled      bool   `json:"enabled"`
}

type TrackerLink struct {
	MediaType   MediaType `json:"mediaType"`
	MediaData   int64     `json:"mediaData"`
	IDTracker   int64     `json:"idTracker"`
	TrackerData string    `json:"trackerData"`
	Enabled     bool      `json:"enabled"`
}

type TvShow struct {
	ID          int64  `json:"id"`
	Title       string `json:"title"`
	Overview    string `json:"overview"`
	Icon        string `json:"icon"`
	Fanart      string `json:"fanart"`
	Rating      int64  `json:"rating"`
	Premiered   int64  `json:"premiered"`
	Trailer     string `json:"trailer"`
	Website     string `json:"website"`
	ScraperName string `json:"scraperName"`
	ScraperID   string `json:"scraperID"`
	ScraperData string `json:"scraperData"`
	ScraperLink string `json:"scraperLink"`
	Path        string `json:"path"`
	IDLib       int64  `json:"idLib"`
	AddDate     int64  `json:"addDate"`
	UpdateDate  int64  `json:"updateDate"`
	UpdateMode  int64  `json:"updateMode"`
}

type Upcoming struct {
	ID           int64     `json:"id"`
	MediaType    MediaType `json:"mediaType"`
	RefMediaData int64     `json:"refMediaData"`
	Title        string    `json:"title"`
	Overview     string    `json:"overview"`
	Icon         string    `json:"icon"`
	Date         int64     `json:"date"`
}

type User struct {
	ID       int64  `json:"id"`
	Name     string `json:"name"`
	Username string `json:"username"`
	Password string `json:"password"`
	Enabled  bool   `json:"enabled"`
}

type VideoFile struct {
	ID         int64           `json:"id"`
	IDLib      int64           `json:"idLib"`
	MediaType  MediaType       `json:"mediaType"`
	MediaData  int64           `json:"mediaData"`
	Path       string          `json:"path"`
	Format     string          `json:"format"`
	Duration   float64         `json:"duration"`
	Extension  string          `json:"extension"`
	Video      json.RawMessage `json:"video"`
	Audio      json.RawMessage `json:"audio"`
	Subtitle   json.RawMessage `json:"subtitle"`
	Size       float64         `json:"size"`
	Tmp        bool            `json:"tmp"`
	AddDate    int64           `json:"addDate"`
	UpdateDate int64           `json:"updateDate"`
}
