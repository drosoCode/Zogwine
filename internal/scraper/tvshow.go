package scraper

import (
	"errors"

	"github.com/Zogwine/Zogwine/internal/scraper/types"
	"github.com/Zogwine/Zogwine/internal/util"
)

func LoadTVSPlugins() ([]types.TVShowProvider, error) {
	pluginsInterfaces, err := util.LoadPlugins("TVShowProvider", "plugins/scraper/")
	if err != nil {
		return nil, err
	}
	var plugins []types.TVShowProvider
	for _, plInterface := range pluginsInterfaces {
		pl, ok := plInterface.(func() types.TVShowProvider)
		if ok {
			plugins = append(plugins, pl())
		}
	}
	return plugins, nil
}

func LoadTVSPlugin(name string) (types.TVShowProvider, error) {
	pl, err := util.LoadPlugin("TVShowProvider", "plugins/"+name+".go", nil)
	if err != nil {
		return nil, err
	}
	p, ok := pl.(func() types.TVShowProvider)
	if ok {
		return nil, errors.New("error")
	}
	return p(), nil
}
