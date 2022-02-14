package common

type PersonProvider interface {
	Provider
	SearchPerson(name string) ([]SearchData, error)
	GetPersonDetails() (PersonDetailsData, error)
}

type PersonDetailsData struct {
	Birthdate   int64
	Deathdate   int64
	Gender      int
	Description string
	Icon        string
	KnownFor    string
	ScraperInfo
}
