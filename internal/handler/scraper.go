package handler

import (
	"context"
	"net/http"
	"strconv"

	"github.com/Zogwine/Zogwine/internal/auth"
	database "github.com/Zogwine/Zogwine/internal/database"
	"github.com/Zogwine/Zogwine/internal/scraper"
	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util/srv"
	"github.com/go-chi/chi/v5"
)

func SetupScraper(r chi.Router, s *status.Status) {
	scr := chi.NewRouter()
	r.Mount("/scraper", scr)
	scr.Use(auth.CheckUserMiddleware(s, "admin"))
	scr.Get("/result", ListScraperResults(s))
	scr.Get("/result/{mediatype}", ListScraperResultsForType(s))
	scr.Get("/result/{mediatype}/{mediadata}", GetScraperResultsForMedia(s))
	scr.Post("/result/{mediatype}/{mediadata}/{id}", SelectScraperResult(s))
	scr.Post("/scan/{mediatype}", StartScraperScan(s))
	scr.Post("/scan/{mediatype}/{id}", StartScraperScan(s))
}

// GET scraper/result
func ListScraperResults(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		selec, err := s.DB.ListMultipleResults(context.Background())
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, selec)
	}
}

// GET scraper/result/{mediatype}
func ListScraperResultsForType(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		selec, err := s.DB.ListMultipleResultsByMediaType(context.Background(), database.MediaType(chi.URLParam(r, "mediatype")))
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, selec)
	}
}

// GET scraper/result/{mediatype}/{mediadata}
func GetScraperResultsForMedia(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		mediaData, _ := strconv.ParseInt(chi.URLParam(r, "mediadata"), 10, 64)
		selec, err := s.DB.GetMultipleResultsByMedia(context.Background(), database.GetMultipleResultsByMediaParams{
			MediaType: database.MediaType(chi.URLParam(r, "mediatype")),
			MediaData: mediaData,
		})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, selec)
	}
}

// POST scraper/result/{mediatype}/{mediadata}/{id}
func SelectScraperResult(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		mediaData, _ := strconv.ParseInt(chi.URLParam(r, "mediadata"), 10, 64)
		id, _ := strconv.Atoi(chi.URLParam(r, "id"))
		_, err := scraper.SelectScraperResult(s, database.MediaType(chi.URLParam(r, "mediatype")), mediaData, id)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, "ok")
	}
}

// POST scraper/scan/{mediatype}
// POST scraper/scan/{mediatype}/{idlib}
func StartScraperScan(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := int64(0)
		i := chi.URLParam(r, "id")
		if i != "" {
			id, _ = strconv.ParseInt(i, 10, 64)
		}

		conf := scraper.ScraperScanConfig{
			AutoAdd:            false,
			AddUnknown:         false,
			MaxConcurrentScans: s.Config.Analyzer.Video.MaxConcurrentScans,
		}

		if r.URL.Query().Get("autoadd") == "true" {
			conf.AutoAdd = true
		}
		if r.URL.Query().Get("addunknown") == "true" {
			conf.AddUnknown = true
		}

		err := scraper.StartScan(s, database.MediaType(chi.URLParam(r, "mediatype")), id, conf)

		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, "ok")
	}
}
