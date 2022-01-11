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

func SetupCore(r chi.Router, s *status.Status) {
	core := chi.NewRouter()
	r.Mount("/core", core)
	core.Get("/statistic", GetStats(s))
}

type stats struct {
	database.GetEpisodeStatRow
	database.GetTVShowStatRow
	database.GetMovieStatRow
	TotalTime int64 `json:"totalTime"`
}

// GET core/statistic
func GetStats(s *status.Status) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token, err := auth.GetToken(r)
		if srv.IfError(w, r, err) {
			return
		}
		uid, err := auth.GetUserID(s, token)
		if srv.IfError(w, r, err) {
			return
		}

		var stat stats
		ctx := context.Background()

		epStats, err := s.DB.GetEpisodeStat(ctx, uid)
		if srv.IfError(w, r, err) {
			return
		}
		stat.EpisodeCount = epStats.EpisodeCount
		stat.WatchedEpisode = epStats.WatchedEpisode
		stat.WatchedEpisodeCount = epStats.WatchedEpisodeCount
		stat.EpisodeTime = epStats.EpisodeTime

		tvsStats, err := s.DB.GetTVShowStat(ctx, uid)
		if srv.IfError(w, r, err) {
			return
		}
		stat.TvsCount = tvsStats.TvsCount
		stat.WatchedTvs = tvsStats.WatchedTvs

		movStats, err := s.DB.GetMovieStat(ctx, uid)
		if srv.IfError(w, r, err) {
			return
		}
		stat.MovieCount = movStats.MovieCount
		stat.WatchedMovie = movStats.WatchedMovie
		stat.WatchedMovieCount = movStats.WatchedMovieCount
		stat.MovieTime = movStats.MovieTime

		stat.TotalTime = stat.EpisodeTime + stat.MovieTime

		srv.JSON(w, r, 200, stat)
	}
}
