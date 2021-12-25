package handler

import (
	"net/http"

	"github.com/Zogwine/Zogwine/internal/auth"
	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util/srv"
	"github.com/go-chi/chi/v5"
)

func SetupUser(r chi.Router, s *status.Status) {
	usr := chi.NewRouter()
	r.Mount("/user", usr)
	usr.Post("/login", LoginUser(s))
	usr.Get("/logout", LogoutUser(s))
	usr.Get("/data", DataUser(s))
}

func LoginUser(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {

		uid, err := auth.Authenticate(r, s)
		if srv.IfError(w, r, err) {
			return
		}
		token := auth.Login(s, uid)

		type tokenReturn struct {
			Token string `json:"token"`
		}

		srv.JSON(w, r, 200, tokenReturn{Token: token})
	}
}

func LogoutUser(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token, err := auth.GetToken(r)
		if srv.IfError(w, r, err) {
			return
		}
		auth.Logout(s, token)

		srv.JSON(w, r, 200, "ok")
	}
}

func DataUser(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		srv.JSON(w, r, 200, "ok")
	}
}
