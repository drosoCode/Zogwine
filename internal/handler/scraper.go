package handler

import (
	"github.com/Zogwine/Zogwine/internal/auth"
	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/go-chi/chi/v5"
)

func SetupScraper(r chi.Router, s *status.Status) {
	scr := chi.NewRouter()
	r.Mount("/scraper", scr)
	scr.Use(auth.CheckUserMiddleware(s, "admin"))

}
