package common

type FillerType int

const (
	Canon      FillerType = 0 // canon with the original support (lightnovel, manga, ...)
	Adaptation FillerType = 1 // canon in the adaptation (ex: anime with a diverging story)
	Mixed      FillerType = 2 // only a part of the episode is not canon
	Filler     FillerType = 3 // nothing related to the original support
)

type FillerData struct {
	Filler FillerType
	Index  int // absolute number since the start of the serie (ex: if s1 contains 20 ep and we want the 3rd ep of s2, index will be: 23)
}

type FillerProvider interface {
	Provider
	NewFillerProvider() FillerProvider
	SearchFiller(name string) ([]SearchData, error)
	GetFiller() (FillerData, error)
}
