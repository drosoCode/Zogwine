package handler

import (
	"context"
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

	tvs.Get("/{id}/season", ListTVSSeason(s))
	tvs.Get("/{id}/season/{season}", GetTVSSeason(s))
	tvs.Put("/{id}/season/{season}", UpdateTVSSeason(s))
	tvs.Delete("/{id}/season/{season}", DeleteTVSSeason(s))

	tvs.Get("/episode/{id}", GetTVSEpisode(s))
	tvs.Get("/{id}/season/{season}/episode", ListTVSEpisodeBySeason(s))
	tvs.Get("/{id}/episode", ListTVSEpisode(s))
	tvs.Put("/episode/{id}", UpdateTVSEpisode(s))
	tvs.Delete("/episode/{id}", DeleteTVSEpisode(s))

	tvs.Put("/{id}/season/{season}/status", UpdateTVSSeasonStatus(s))
	tvs.Put("/episode/{id}/status", UpdateTVSEpisodeStatus(s))
}

// tv shows management

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

// seasons managements

// GET tvs/{id}/season/
func ListTVSSeason(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		shows, err := s.DB.ListShowSeason(r.Context(), database.ListShowSeasonParams{IDUser: userInfo.ID, IDShow: id})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET tvs/{id}/season/{season}
func GetTVSSeason(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)

		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}
		season, err := strconv.ParseInt(chi.URLParam(r, "season"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		shows, err := s.DB.GetShowSeason(r.Context(), database.GetShowSeasonParams{IDUser: userInfo.ID, IDShow: id, Season: season})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// PUT tvs/{id}/season/{season}
func UpdateTVSSeason(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}
		season, err := strconv.ParseInt(chi.URLParam(r, "season"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		updateData := database.UpdateShowSeasonParams{}
		err = json.NewDecoder(r.Body).Decode(&updateData)
		if srv.IfError(w, r, err) {
			return
		}

		// add additionnal info to updateData struct
		updateData.IDShow = id
		updateData.Season = season
		updateData.UpdateDate = time.Now().Unix()

		err = s.DB.UpdateShowSeason(r.Context(), updateData)
		if srv.IfError(w, r, err) {
			return
		}

		srv.JSON(w, r, 200, "ok")
	}
}

// DELETE tvs/{id}/season/{season}
func DeleteTVSSeason(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}
		season, err := strconv.ParseInt(chi.URLParam(r, "season"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		err = s.DB.DeleteShowStatusBySeason(r.Context(), database.DeleteShowStatusBySeasonParams{IDShow: id, Season: season})
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteShowFileBySeason(r.Context(), database.DeleteShowFileBySeasonParams{IDShow: id, Season: season})
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteShowEpisodeBySeason(r.Context(), database.DeleteShowEpisodeBySeasonParams{IDShow: id, Season: season})
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteShowSeasonByNum(r.Context(), database.DeleteShowSeasonByNumParams{IDShow: id, Season: season})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, "ok")
	}
}

// episode management

// GET tvs/episode/{id}/
func GetTVSEpisode(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		shows, err := s.DB.GetShowEpisode(r.Context(), database.GetShowEpisodeParams{IDUser: userInfo.ID, ID: id})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET tvs/{id}/episode
func ListTVSEpisode(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		shows, err := s.DB.ListShowEpisode(r.Context(), database.ListShowEpisodeParams{IDUser: userInfo.ID, IDShow: id})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET tvs/{id}/season/{season}/episode
func ListTVSEpisodeBySeason(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}
		season, err := strconv.ParseInt(chi.URLParam(r, "season"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		shows, err := s.DB.ListShowEpisodeBySeason(r.Context(), database.ListShowEpisodeBySeasonParams{IDUser: userInfo.ID, IDShow: id, Season: season})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// PUT tvs/episode/{id}
func UpdateTVSEpisode(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		updateData := database.UpdateShowEpisodeParams{}
		err = json.NewDecoder(r.Body).Decode(&updateData)
		if srv.IfError(w, r, err) {
			return
		}

		// add additionnal info to updateData struct
		updateData.ID = id
		updateData.UpdateDate = time.Now().Unix()

		err = s.DB.UpdateShowEpisode(r.Context(), updateData)
		if srv.IfError(w, r, err) {
			return
		}

		srv.JSON(w, r, 200, "ok")
	}
}

// DELETE tvs/episode/{id}
func DeleteTVSEpisode(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		err = s.DB.DeleteShowStatusByEpisode(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteShowFileByEpisode(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteShowEpisodeByID(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, "ok")
	}
}

// status helpers

// PUT tvs/{id}/season/{season}/status
func UpdateTVSSeasonStatus(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)

		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}
		season, err := strconv.ParseInt(chi.URLParam(r, "season"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}
		mode := r.URL.Query().Get("mode")

		eps, err := s.DB.ListShowEpisodeBySeason(r.Context(), database.ListShowEpisodeBySeasonParams{IDUser: userInfo.ID, IDShow: id, Season: season})
		if srv.IfError(w, r, err) {
			return
		}

		nbWatched := 0
		for _, data := range eps {
			nbWatched += int(data.WatchCount)
		}

		if mode != "1" && mode != "0" {
			if nbWatched > 0 {
				mode = "0"
			} else {
				mode = "1"
			}
		}

		for _, data := range eps {
			toggleEpisodeStatus(s, userInfo.ID, data.ID, mode)
		}

		srv.JSON(w, r, 200, "ok")
	}
}

// PUT tvs/episode/{id}/status
func UpdateTVSEpisodeStatus(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)

		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}
		mode := r.URL.Query().Get("mode")
		err = toggleEpisodeStatus(s, userInfo.ID, id, mode)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, "ok")
	}
}

func toggleEpisodeStatus(s *status.Status, idUser int64, idEpisode int64, mode string) error {
	ctx := context.Background()
	var watchCount int64
	if mode == "1" {
		// set all watched
		watchCount = 1
	} else if mode == "0" {
		// set all not watched
		watchCount = 0
	} else {
		// toggle
		data, err := s.DB.GetMediaStatus(ctx, database.GetMediaStatusParams{IDUser: idUser, MediaType: database.MediaTypeTvsEpisode, MediaData: idEpisode})
		if err != nil || data.WatchCount == 0 {
			watchCount = 1
		} else {
			watchCount = 0
		}
	}
	return s.DB.UpdateMediaStatus(ctx, database.UpdateMediaStatusParams{IDUser: idUser, MediaType: database.MediaTypeTvsEpisode, MediaData: idEpisode, WatchCount: watchCount, WatchTime: 0, LastDate: time.Now().Unix()})
}
