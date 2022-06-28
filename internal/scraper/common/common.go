package common

import log "github.com/sirupsen/logrus"

type Provider interface {
	Setup(config map[string]string, logger *log.Logger) error
	Configure(ScraperID string, ScraperData string)
}

type ScraperInfo struct {
	ScraperID   string `json:"scraperID"`
	ScraperName string `json:"scraperName"`
	ScraperData string `json:"scraperData"`
	ScraperLink string `json:"scraperLink"`
}

type TagData struct {
	Name  string `json:"name"`
	Value string `json:"value"`
	Icon  string `json:"icon"`
}

type PersonData struct {
	Name        string `json:"name"`
	Role        string `json:"role"`
	IsCharacter bool   `json:"isCharacter"`
}

type SearchData struct {
	Title     string `json:"title"`
	Overview  string `json:"overview"`
	Icon      string `json:"icon"`
	Premiered int64  `json:"premiered"`
	ScraperInfo
}

type UpcomingData struct {
	Title     string `json:"title"`
	Overview  string `json:"overview"`
	Icon      string `json:"icon"`
	Premiered int64  `json:"premiered"`
	ID1       int64  `json:"id1"` // season for tvs
	ID2       int64  `json:"id2"` // episode for tvs
	ScraperInfo
}
