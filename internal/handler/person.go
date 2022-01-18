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

func SetupPerson(r chi.Router, s *status.Status) {
	pers := chi.NewRouter()
	r.Mount("/person", pers)
	pers.Use(auth.CheckUserMiddleware(s))

	pers.Get("/{id}", GetPerson(s))
	pers.Get("/name/{name}", ListPersonByName(s))
	pers.Get("/letter/{letter}", ListPersonByLetter(s))
	pers.Get("/{mediaType}/{mediaData}", ListPersonByMedia(s))
	pers.Get("/role/{id}", ListPersonByRole(s))
}

// GET person/{id}
func GetPerson(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		ctx := context.Background()
		shows, err := s.DB.GetPerson(ctx, id)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET person/name/{name}
func ListPersonByName(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := context.Background()
		shows, err := s.DB.ListPersonByName(ctx, "%"+chi.URLParam(r, "name")+"%")
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET person/letter/{letter}
func ListPersonByLetter(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := context.Background()
		shows, err := s.DB.ListPersonByName(ctx, "%"+chi.URLParam(r, "letter"))
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET person/{mediaType}/{mediaData}
func ListPersonByMedia(s *status.Status) http.HandlerFunc {
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
		shows, err := s.DB.ListPersonByMedia(ctx, database.ListPersonByMediaParams{MediaType: mediaType, MediaData: mediaData})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET person/role/{id}
func ListPersonByRole(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}
		ctx := context.Background()
		shows, err := s.DB.ListPersonByRole(ctx, id)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}
