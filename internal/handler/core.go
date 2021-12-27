package handler

import (
	"encoding/base64"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util/srv"
	"github.com/go-chi/chi/v5"
)

func SetupCore(r chi.Router, s *status.Status) {
	usr := chi.NewRouter()
	r.Mount("/core", usr)
	usr.Get("/image/{id}", CoreImage(s))
}

func CoreImage(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		if id != "" {
			path := filepath.Join(s.Config.Server.CachePath, id)
			if _, err := os.Stat(path); err == nil {
				// if the file exists in the cache, return it
				srv.SendFile(w, r, path, "image/jpeg")
				return
			}

			// else, decode the base64 id
			// make sure that the padding is correct
			if i := len(id) % 4; i != 0 {
				id += strings.Repeat("=", 4-i)
			}
			url, err := base64.StdEncoding.DecodeString(id)
			if srv.IfError(w, r, err) {
				return
			}
			surl := string(url)
			// if this id is a valid url, return a 302
			if surl[0:4] == "http" {
				w.Header().Set("Location", surl)
				w.WriteHeader(302)
				return
			}

			// else, return a 404
			srv.Error(w, r, 404, "Not Found")
			return
		}

	}
}
