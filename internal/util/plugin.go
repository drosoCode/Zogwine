package util

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"

	"github.com/Zogwine/Zogwine/internal/util/symbol"
	"github.com/traefik/yaegi/interp"
	"github.com/traefik/yaegi/stdlib"
)

func LoadPlugins(pluginType string, folder string) ([]interface{}, error) {

	i := interp.New(interp.Options{})
	i.Use(stdlib.Symbols)
	i.Use(symbol.Symbols)

	var plugins []interface{}

	err := filepath.Walk(folder, func(path string, info os.FileInfo, err error) error {
		pl, err := LoadPlugin(pluginType, path, i)
		if err == nil {
			plugins = append(plugins, pl)
		}
		return nil
	})

	return plugins, err
}

func LoadPlugin(pluginType string, path string, i *interp.Interpreter) (interface{}, error) {

	if i == nil {
		i = interp.New(interp.Options{})
		i.Use(stdlib.Symbols)
		i.Use(symbol.Symbols)
	}

	if filepath.Ext(path) != ".go" {
		return nil, errors.New("invalid file extension")
	}

	fmt.Println(path)
	file, err := os.ReadFile(path)
	if err != nil {
		return nil, errors.New("unable to read file")
	}

	_, err = i.Eval(string(file))
	if err != nil {
		return nil, errors.New("unable to eval file")
	}

	packageName := filepath.Base(filepath.Dir(path))

	constructor := packageName + ".New" + pluginType

	v, err := i.Eval(constructor)
	if err != nil {
		return nil, errors.New("unable to instanciate plugin with " + constructor)
	}

	return v.Interface(), nil
}
