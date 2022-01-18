package handler

import (
	"context"
	"net/http"
	"strconv"

	"github.com/Zogwine/Zogwine/internal/auth"
	database "github.com/Zogwine/Zogwine/internal/database"
	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util/srv"
	"github.com/go-chi/chi/v5"
)

// handle tags
func SetupTag(r chi.Router, s *status.Status) {
	tag := chi.NewRouter()
	r.Mount("/tag", tag)
	tag.Use(auth.CheckUserMiddleware(s))

	tag.Get("/{id}", GetTag(s))
	tag.Get("/category/{id}", ListTagCatg(s))
	tag.Get("/category/{catg}", ListTagByCatg(s))
}

// tag management

// GET tag/{id}
func GetTag(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		ctx := context.Background()
		shows, err := s.DB.GetTag(ctx, id)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET tag/category
func ListTagCatg(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := context.Background()
		shows, err := s.DB.ListTagCatg(ctx)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET tag/category/{catg}
func ListTagByCatg(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := context.Background()
		shows, err := s.DB.ListTagByCatg(ctx, chi.URLParam(r, "catg"))
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET tag/{mediaType}/{mediaData}
func ListTagByMedia(s *status.Status) http.HandlerFunc {
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
		shows, err := s.DB.ListTagByMedia(ctx, database.ListTagByMediaParams{MediaType: mediaType, MediaData: mediaData})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}
