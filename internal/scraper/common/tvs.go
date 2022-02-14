package common

type TVShowProvider interface {
	Provider
	SearchTVS(name string) ([]SearchData, error)
	GetTVS() (TVSData, error)
	GetTVSSeason(season int) (TVSSeasonData, error)
	//GetTVSEpisode(season int, episode int) (TVSEpisodeData, error)
	//ListTVSTag() ([]TagData, error)
	//ListTVSPerson() ([]PersonData, error)
	//GetTVSUpcomingEpisode() (UpcomingData, error)
}

type TVSData struct {
	Title     string
	Overview  string
	Icon      string
	Fanart    string
	Website   string
	Trailer   string
	Premiered int64
	Rating    int64
	ScraperInfo
}

type TVSSeasonData struct {
	Title     string
	Overview  string
	Icon      string
	Fanart    string
	Trailer   string
	Premiered int64
	Rating    int64
	ScraperInfo
}

type TVSEpisodeData struct {
	Title     string
	Overview  string
	Icon      string
	Premiered int64
	Rating    int64
	Season    int64
	Episode   int64
	ScraperInfo
}
