package common

type MovieProvider interface {
	Provider
	SearchMovie(name string, year int) ([]SearchData, error)
	ListMovieTag() ([]TagData, error)
	ListMoviePerson() ([]PersonData, error)
	GetMovie() (MovieData, error)
	GetMovieUpcoming() (UpcomingData, error)
	GetMovieCollection() (MovieCollectionData, error)
}

type MovieData struct {
	Title      string `json:"title"`
	Overview   string `json:"overview"`
	Icon       string `json:"icon"`
	Fanart     string `json:"fanart"`
	Website    string `json:"website"`
	Trailer    string `json:"trailer"`
	Premiered  int64  `json:"premiered"`
	Rating     int64  `json:"rating"`
	Collection int64  `json:"collection"`
	ScraperInfo
}

type MovieCollectionData struct {
	Title     string `json:"title"`
	Overview  string `json:"overview"`
	Icon      string `json:"icon"`
	Fanart    string `json:"fanart"`
	Premiered int64  `json:"premiered"`
	Rating    int64  `json:"rating"`
	ScraperInfo
}
