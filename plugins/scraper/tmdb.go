package scraper

import (
	"github.com/Zogwine/Zogwine/internal/scraper"
	"github.com/Zogwine/Zogwine/internal/scraper/types"
)

type TMDB struct {
	scraper.BaseProvider
	types.MovieProvider
	types.TVShowProvider
	types.PersonProvider
}
