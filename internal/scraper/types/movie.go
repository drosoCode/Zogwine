package types

import "time"

type MovieProvider interface {
	Provider
	NewMovieProvider() MovieProvider
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
	Premiered  time.Time
	Rating     int
	Collection int
	ScraperInfo
}

type MovieCollectionData struct {
	Title     string
	Overview  string
	Icon      string
	Fanart    string
	Premiered time.Time
	Rating    int
	ScraperInfo
}
