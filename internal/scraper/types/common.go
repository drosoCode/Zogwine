package types

import "time"

type Provider interface {
	Setup(config map[string]interface{}) error
	Configure(ScraperID string, ScraperData string) error
}

type ScraperInfo struct {
	ScraperID   string
	ScraperName string
	ScraperData string
	ScraperLink string
}

type TagData struct {
	Name  string
	Value string
	Icon  string
}

type PersonData struct {
	Name        string
	Role        string
	IsCharacter bool
}

type SearchData struct {
	Title     string
	Overview  string
	Icon      string
	Premiered time.Time
	ScraperInfo
}

type UpcomingData struct {
	Title     string
	Overview  string
	Icon      string
	Premiered string
	ScraperInfo
}
