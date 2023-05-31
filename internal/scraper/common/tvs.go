package common

type TVShowProvider interface {
	Provider
	SearchTVS(name string) ([]SearchData, error)
	GetTVS() (TVSData, error)
	GetTVSSeason(season int) (TVSSeasonData, error)
	GetTVSEpisode(season int, episode int) (TVSEpisodeData, error)
	ListTVSTag() ([]TagData, error)
	ListTVSPerson() ([]PersonData, error)
	GetTVSUpcoming() (UpcomingData, error)
}

type TVSData struct {
	Title     string `json:"title"`
	Overview  string `json:"overview"`
	Icon      string `json:"icon"`
	Fanart    string `json:"fanart"`
	Website   string `json:"website"`
	Trailer   string `json:"trailer"`
	Premiered int64  `json:"premiered"`
	Rating    int64  `json:"rating"`
	ScraperInfo
}

type TVSSeasonData struct {
	Title     string `json:"title"`
	Overview  string `json:"overview"`
	Icon      string `json:"icon"`
	Fanart    string `json:"fanart"`
	Trailer   string `json:"trailer"`
	Premiered int64  `json:"premiered"`
	Rating    int64  `json:"rating"`
	ScraperInfo
}

type TVSEpisodeData struct {
	Title     string `json:"title"`
	Overview  string `json:"overview"`
	Icon      string `json:"icon"`
	Premiered int64  `json:"premiered"`
	Rating    int64  `json:"rating"`
	Season    int64  `json:"season"`
	Episode   int64  `json:"episode"`
	ScraperInfo
}
