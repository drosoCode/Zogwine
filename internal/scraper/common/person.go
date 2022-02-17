package common

type PersonProvider interface {
	Provider
	SearchPerson(name string) ([]SearchData, error)
	GetPerson() (PersonDetails, error)
}

type PersonDetails struct {
	Birthdate   int64
	Deathdate   int64
	Gender      int64
	Name        string
	Description string
	Icon        string
	KnownFor    string
	Rating      int64
	ScraperInfo
}
