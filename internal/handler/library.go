package handler

import (
	"net/http"
	"strconv"

	"github.com/Zogwine/Zogwine/internal/auth"
	database "github.com/Zogwine/Zogwine/internal/database"
	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util/srv"
	"github.com/go-chi/chi/v5"
)

func SetupLibrary(r chi.Router, s *status.Status) {
	mov := chi.NewRouter()
	r.Mount("/library", mov)
	mov.Use(auth.CheckUserMiddleware(s))

	mov.Get("/", ListLibrary(s))
	mov.Get("/{id}", GetLibrary(s))
}

// movies management

// GET library/
func ListLibrary(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var libs []database.Library
		var err error

		if mt := r.URL.Query().Get("mediatype"); mt != "" {
			mediaType, _ := strconv.ParseInt(mt, 10, 64)
			libs, err = s.DB.ListLibraryWithType(r.Context(), database.MediaType(database.MediaTypeInt[mediaType]))
			if srv.IfError(w, r, err) {
				return
			}
		} else {
			libs, err = s.DB.ListLibrary(r.Context())
			if srv.IfError(w, r, err) {
				return
			}
		}
		srv.JSON(w, r, 200, libs)
	}
}

// GET library/{id}
func GetLibrary(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		lib, err := s.DB.GetLibrary(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, lib)
	}
}
