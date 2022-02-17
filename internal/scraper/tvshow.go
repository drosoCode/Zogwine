package scraper

import (
	"errors"
	"fmt"

	log "github.com/sirupsen/logrus"

	"github.com/Zogwine/Zogwine/internal/scraper/common"
	"github.com/Zogwine/Zogwine/internal/util"
)

func LoadTVSPlugins() ([]common.TVShowProvider, error) {
	pluginsInterfaces, err := util.LoadPlugins("TVShowProvider", "plugins/scraper/")
	if err != nil {
		return nil, err
	}
	var plugins []common.TVShowProvider
	for _, plInterface := range pluginsInterfaces {
		pl, ok := plInterface.(func() common.TVShowProvider)
		if ok {
			plugins = append(plugins, pl())
		}
	}
	return plugins, nil
}

func LoadTVSPlugin(name string) (common.TVShowProvider, error) {
	pl, err := util.LoadPlugin("TVShowProvider", "./plugins/scraper/"+name)
	if err != nil {
		return nil, err
	}
	p, ok := pl.(func() common.TVShowProvider)
	if !ok {
		return nil, errors.New("error type assertion failed")
	}
	return p(), nil
}

func Test(logger *log.Logger) {
	pl, err := LoadTVSPlugin("tmdb")

	if err != nil {
		fmt.Println(err)
	}

	conf := map[string]string{
		"api_key": "",
	}

	pl.Setup(conf, logger)
	pl.Configure("1429", "")

}
