package handler

import (
	"context"
	"net/http"

	"github.com/Zogwine/Zogwine/internal/auth"
	database "github.com/Zogwine/Zogwine/internal/database"
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

type UserData struct {
	database.GetUserRow
	UserGroup   []string `json:"userGroup"`
	SystemGroup []string `json:"systemGroup"`
}

func DataUser(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token, err := auth.GetToken(r)
		if srv.IfError(w, r, err) {
			return
		}
		uid, err := auth.GetUserID(s, token)
		if srv.IfError(w, r, err) {
			return
		}

		var data UserData
		ctx := context.Background()

		user, err := s.DB.GetUser(ctx, uid)
		if srv.IfError(w, r, err) {
			return
		}

		data.Enabled = user.Enabled
		data.ID = user.ID
		data.Name = user.Name
		data.Username = user.Username

		data.UserGroup, err = s.DB.ListGroupFromUser(ctx, database.ListGroupFromUserParams{ID: uid, System: false})
		if srv.IfError(w, r, err) {
			return
		}

		data.SystemGroup, err = s.DB.ListGroupFromUser(ctx, database.ListGroupFromUserParams{ID: uid, System: true})
		if srv.IfError(w, r, err) {
			return
		}

		srv.JSON(w, r, 200, data)
	}
}
