package types

import "time"

type TVShowProvider interface {
	Provider
	NewTVShowProvider() TVShowProvider
	SearchTVS(name string) ([]SearchData, error)
	GetTVSEpisode(season int, episode int) (TVSEpisodeData, error)
	ListTVSTag() ([]TagData, error)
	ListTVSPerson() ([]PersonData, error)
	GetTVSSeason(season int) (TVSSeasonData, error)
	GetTVS() (TVSData, error)
	GetTVSUpcomingEpisode() (UpcomingData, error)
}

type TVSData struct {
	Title     string
	Overview  string
	Icon      string
	Fanart    string
	Premiered time.Time
	Rating    int
	ScraperInfo
}

type TVSSeasonData struct {
	Title     string
	Overview  string
	Icon      string
	Fanart    string
	Premiered time.Time
	Rating    int
	ScraperInfo
}

type TVSEpisodeData struct {
	Title     string
	Overview  string
	Icon      string
	Premiered time.Time
	Rating    int
	Season    int
	Episode   int
	ScraperInfo
}
