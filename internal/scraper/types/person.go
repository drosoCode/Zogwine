package types

import "time"

type PersonProvider interface {
	Provider
	NewPersonProvider() PersonProvider
	SearchPerson(name string) ([]SearchData, error)
	GetPersonDetails() (PersonDetailsData, error)
}

type PersonDetailsData struct {
	Birthdate   time.Time
	Deathdate   time.Time
	Gender      int
	Description string
	Icon        string
	KnownFor    string
	ScraperInfo
}
