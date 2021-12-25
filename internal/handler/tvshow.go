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

func SetupTVS(r chi.Router, s *status.Status) {
	tvs := chi.NewRouter()
	r.Mount("/tvs", tvs)
	tvs.Use(auth.CheckUserMiddleware(s, "tvs"))

	tvs.Get("/", ListTVS(s))
	tvs.Get("/{id}", GetTVS(s))
}

func GetTVS(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)

		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		shows, err := s.DB.GetShow(r.Context(), database.GetShowParams{IDUser: userInfo.ID, ID: id})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

func ListTVS(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)

		shows, err := s.DB.ListShow(r.Context(), userInfo.ID)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}
