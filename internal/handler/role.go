package handler

import (
	"context"
	"net/http"
	"strconv"

	"github.com/Zogwine/Zogwine/internal/auth"
	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util/srv"
	"github.com/go-chi/chi/v5"
)

func SetupRole(r chi.Router, s *status.Status) {
	role := chi.NewRouter()
	r.Mount("/role", role)
	role.Use(auth.CheckUserMiddleware(s))

	role.Get("/{id}", GetRole(s))
	role.Get("/name/{name}", ListRoleByName(s))
	role.Get("/letter/{letter}", ListRoleByLetter(s))
	role.Get("/person/{id}", ListRoleByPerson(s))
}

// GET role/{id}
func GetRole(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		ctx := context.Background()
		shows, err := s.DB.GetRole(ctx, id)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET role/name/{name}
func ListRoleByName(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := context.Background()
		shows, err := s.DB.ListRoleByName(ctx, "%"+chi.URLParam(r, "name")+"%")
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET person/letter/{letter}
func ListRoleByLetter(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := context.Background()
		shows, err := s.DB.ListRoleByName(ctx, "%"+chi.URLParam(r, "letter"))
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET role/person/{id}
func ListRoleByPerson(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}
		ctx := context.Background()
		shows, err := s.DB.ListRoleByPerson(ctx, id)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}
