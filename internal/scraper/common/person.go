package common

type PersonProvider interface {
	Provider
	SearchPerson(name string) ([]SearchData, error)
	GetPerson() (PersonDetails, error)
}

type PersonDetails struct {
	Birthdate   int64  `json:"birthdate"`
	Deathdate   int64  `json:"deathdate"`
	Gender      int64  `json:"gender"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Icon        string `json:"icon"`
	KnownFor    string `json:"knownFor"`
	Rating      int64  `json:"rating"`
	ScraperInfo
}
