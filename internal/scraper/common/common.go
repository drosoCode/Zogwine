package common

import log "github.com/sirupsen/logrus"

type Provider interface {
	Setup(config map[string]string, logger *log.Logger) error
	Configure(ScraperID string, ScraperData string)
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
	Premiered int64
	ScraperInfo
}

type UpcomingData struct {
	Title     string
	Overview  string
	Icon      string
	Premiered string
	ScraperInfo
}
