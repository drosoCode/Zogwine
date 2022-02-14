package common

type MovieProvider interface {
	Provider
	SearchMovie(name string) ([]SearchData, error)
	ListMovieTag() ([]TagData, error)
	ListMoviePerson() ([]PersonData, error)
	GetMovie() (MovieData, error)
	GetMovieUpcoming() (UpcomingData, error)
	GetMovieCollection() (MovieCollectionData, error)
}

type MovieData struct {
	Title      string
	Overview   string
	Icon       string
	Fanart     string
	Website    string
	Trailer    string
	Premiered  int64
	Rating     int
	Collection int
	ScraperInfo
}

type MovieCollectionData struct {
	Title     string
	Overview  string
	Icon      string
	Fanart    string
	Premiered int64
	Rating    int
	ScraperInfo
}
