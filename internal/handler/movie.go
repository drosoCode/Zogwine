package handler

import (
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

func SetupMovie(r chi.Router, s *status.Status) {
	mov := chi.NewRouter()
	r.Mount("/movie", mov)
	mov.Use(auth.CheckUserMiddleware(s, "movie"))

	mov.Get("/", ListMovie(s))
	mov.Get("/{id}", GetMovie(s))
	mov.Get("/collection", ListCollection(s))
	mov.Get("/collection/{id}", GetCollection(s))
	mov.Get("/fromCollection/{id}", ListMovieFromCollection(s))

	mov.Put("/{id}", UpdateMovie(s))
	mov.Put("/{id}/status", UpdateMovieStatus(s))
	mov.Put("/collection/{id}", UpdateCollection(s))

	mov.Delete("/{id}", DeleteMovie(s))
	mov.Delete("/collection/{id}", DeleteCollection(s))
}

// movies management

// GET movie/
func ListMovie(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)

		shows, err := s.DB.ListMovie(r.Context(), userInfo.ID)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET movie/{id}
func GetMovie(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)

		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		shows, err := s.DB.GetMovie(r.Context(), database.GetMovieParams{IDUser: userInfo.ID, ID: id})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET movie/collection
func ListCollection(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)

		shows, err := s.DB.ListCollection(r.Context(), userInfo.ID)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET movie/collection/{id}
func GetCollection(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)

		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		shows, err := s.DB.GetCollection(r.Context(), database.GetCollectionParams{IDUser: userInfo.ID, ID: id})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// GET movie/fromCollection/{id}
func ListMovieFromCollection(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)

		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		shows, err := s.DB.ListMovieFromCollection(r.Context(), database.ListMovieFromCollectionParams{IDCollection: id, IDUser: userInfo.ID})
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, shows)
	}
}

// PUT movie/{id}
func UpdateMovie(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		updateData := database.UpdateMovieParams{}
		err = json.NewDecoder(r.Body).Decode(&updateData)
		if srv.IfError(w, r, err) {
			return
		}

		// add additionnal info to updateData struct
		updateData.ID = id
		updateData.UpdateDate = time.Now().Unix()

		err = s.DB.UpdateMovie(r.Context(), updateData)
		if srv.IfError(w, r, err) {
			return
		}

		srv.JSON(w, r, 200, "ok")
	}
}

// DELETE movie/{id}
func DeleteMovie(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		err = s.DB.DeleteMovieStatus(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteMovieFile(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteMovie(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, "ok")
	}
}

// PUT movie/collection/{id}
func UpdateCollection(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		updateData := database.UpdateMovieCollectionParams{}
		err = json.NewDecoder(r.Body).Decode(&updateData)
		if srv.IfError(w, r, err) {
			return
		}

		// add additionnal info to updateData struct
		updateData.ID = id
		updateData.UpdateDate = time.Now().Unix()

		err = s.DB.UpdateMovieCollection(r.Context(), updateData)
		if srv.IfError(w, r, err) {
			return
		}

		srv.JSON(w, r, 200, "ok")
	}
}

// DELETE movie/collection/{id}
func DeleteCollection(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		err = s.DB.DeleteMovieStatusFromCollection(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteMovieFileFromCollection(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteMovieFromCollection(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		err = s.DB.DeleteMovieCollection(r.Context(), id)
		if srv.IfError(w, r, err) {
			return
		}
		srv.JSON(w, r, 200, "ok")
	}
}

// PUT movie/{id}/status
func UpdateMovieStatus(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userInfo := r.Context().Value(s.CtxUserKey).(auth.UserInfo)

		id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
		if srv.IfError(w, r, err) {
			return
		}

		var watchCount int64
		mode := r.URL.Query().Get("mode")
		if mode == "1" {
			watchCount = 1
		} else if mode == "0" {
			watchCount = 0
		} else {
			data, err := s.DB.GetMediaStatus(r.Context(), database.GetMediaStatusParams{IDUser: userInfo.ID, MediaType: database.MediaTypeMovie, MediaData: id})
			if err != nil || data.WatchCount == 0 {
				watchCount = 1
			} else {
				watchCount = 0
			}
		}

		err = s.DB.UpdateMediaStatus(r.Context(), database.UpdateMediaStatusParams{IDUser: userInfo.ID, MediaType: database.MediaTypeMovie, MediaData: id, WatchCount: watchCount, WatchTime: 0, LastDate: time.Now().Unix()})
		if srv.IfError(w, r, err) {
			return
		}

		srv.JSON(w, r, 200, "ok")
	}
}
