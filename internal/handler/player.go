package handler

import (
	"context"
	"net/http"
	"strconv"

	database "github.com/Zogwine/Zogwine/internal/database"
	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util/srv"
	"github.com/go-chi/chi/v5"
)

func SetupPlayer(r chi.Router, s *status.Status) {
	player := chi.NewRouter()
	r.Mount("/player", player)
	player.Get("/property/{mediaType}/{mediaData}", ListProperties(s))
	player.Get("/property/{id}", GetProperties(s))
}

// GET player/property/{id}
func GetProperties(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}
		ctx := context.Background()
		props, err := s.DB.GetVideoFile(ctx, id)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, props)
	}
}

// GET player/property/{mediaType}/{mediaData}
func ListProperties(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		mediaData, err := strconv.ParseInt(chi.URLParam(r, "mediaData"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}
		mediaTypeInt, err := strconv.ParseInt(chi.URLParam(r, "mediaType"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}
		mediaType := database.MediaType(database.MediaTypeInt[mediaTypeInt])

		ctx := context.Background()
		props, err := s.DB.ListVideoFileFromMedia(ctx, database.ListVideoFileFromMediaParams{MediaType: mediaType, MediaData: mediaData})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, props)
	}
}
