package util

import (
	"archive/zip"
	"errors"
	"os"
	"path/filepath"

	"github.com/Zogwine/Zogwine/internal/util/symbol"
	"github.com/traefik/yaegi/interp"
	"github.com/traefik/yaegi/stdlib"
)

func LoadPlugins(pluginType string, folder string) ([]interface{}, error) {
	var plugins []interface{}

	err := filepath.Walk(folder, func(path string, info os.FileInfo, err error) error {
		pl, err := LoadPlugin(pluginType, path)
		if err == nil {
			plugins = append(plugins, pl)
		}
		if info.IsDir() {
			return filepath.SkipDir
		}
		return nil
	})

	return plugins, err
}

func LoadPlugin(pluginType string, path string) (interface{}, error) {
	var i *interp.Interpreter

	if _, err := os.Stat(path + ".zpk"); err == nil {
		zf, err := zip.OpenReader(path + ".zpk")
		if err != nil {
			return nil, err
		}
		i = interp.New(interp.Options{
			SourcecodeFilesystem: zf,
		})
		path = "./"
	} else if _, err := os.Stat(path); err == nil {
		i = interp.New(interp.Options{})
	} else {
		return nil, errors.New("no plugin found with path: " + path)
	}
	i.Use(stdlib.Symbols)
	i.Use(symbol.Symbols)

	_, err := i.EvalPath(path)
	if err != nil {
		return nil, errors.New("unable to eval file: " + err.Error())
	}

	plugin, ok := i.Symbols(path)[path]["New"+pluginType]
	if !ok {
		return nil, errors.New("invalid plugin")
	}

	return plugin.Interface(), nil
}
