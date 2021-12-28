package handler

import (
	"encoding/base64"
	"encoding/json"
	"net/http"
	"strconv"
	"time"

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
	tvs.Put("/{id}", UpdateTVS(s))
	tvs.Delete("/{id}", DeleteTVS(s))
}

// GET tvs/{id}
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

// GET tvs/
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

// PUT tvs/{id}
func UpdateTVS(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		updateData := database.UpdateShowParams{}
		err = json.NewDecoder(r.Body).Decode(&updateData)
		if srv.IfError(w, r, err) {
			return
		}

		// ensure that the urls to images are base64 encodeds
		if len(updateData.Fanart) > 4 && updateData.Fanart[0:4] == "http" {
			updateData.Fanart = base64.RawStdEncoding.EncodeToString([]byte(updateData.Fanart))
		}
		if len(updateData.Icon) > 4 && updateData.Icon[0:4] == "http" {
			updateData.Icon = base64.RawStdEncoding.EncodeToString([]byte(updateData.Icon))
		}

		// ensure that the library id is valid
		if updateData.IDLib != 0 {
			// TODO
		}

		// add additionnal info to updateData struct
		updateData.ID = id
		updateData.UpdateDate = time.Now().Unix()

		err = s.DB.UpdateShow(r.Context(), updateData)
		if srv.IfError(w, r, err) {
			return
		}

		// apply path changes if needed
		if updateData.Path != "" {
			err = s.DB.UpdateShowPath(r.Context(), database.UpdateShowPathParams{ID: id, RegexpReplace: updateData.Path})
			if srv.IfError(w, r, err) {
				return
			}
		}

		// apply id lib changes if needed
		if updateData.IDLib != 0 {
			err = s.DB.UpdateShowIDLib(r.Context(), database.UpdateShowIDLibParams{IDLib: updateData.IDLib, IDShow: id})
			if srv.IfError(w, r, err) {
				return
			}
		}

		// apply modifications to scrapers
		if updateData.ScraperID != "" || updateData.ScraperName != "" || updateData.ScraperData != "" {

			// some fields may not be present
			userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)
			show, err := s.DB.GetShow(r.Context(), database.GetShowParams{IDUser: userInfo.ID, ID: id})
			if srv.IfError(w, r, err) {
				return
			}
			if updateData.ScraperID == "" {
				updateData.ScraperID = show.ScraperID
			}
			if updateData.ScraperName == "" {
				updateData.ScraperName = show.ScraperName
			}
			if updateData.ScraperData == "" {
				updateData.ScraperData = show.ScraperData
			}

			// TODO: update scraper
			// updateWithSelectionResult(1, id, updateData.ScraperName, updateData.ScraperID, updateData.ScraperData)
		}

		srv.JSON(w, r, 200, "ok")
	}
}

// DELETE tvs/{id}
func DeleteTVS(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		err = s.DB.DeleteShowStatus(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteShowFile(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteShowEpisode(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteShowSeason(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteShow(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, "ok")
	}
}
