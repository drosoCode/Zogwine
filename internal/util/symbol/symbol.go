package symbol

import "reflect"

var Symbols = make(map[string]map[string]reflect.Value)

//go:generate go run github.com/traefik/yaegi/cmd/yaegi extract github.com/Zogwine/Zogwine/internal/scraper/types
