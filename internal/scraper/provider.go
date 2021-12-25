package scraper

import "github.com/Zogwine/Zogwine/internal/scraper/types"

type BaseProvider struct {
	types.Provider
	ScraperID   string
	ScraperData string
}

func (p *BaseProvider) Configure(ScraperID string, ScraperData string) {
	p.ScraperID = ScraperID
	p.ScraperData = ScraperData
}
