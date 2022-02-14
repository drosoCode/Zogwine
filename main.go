package main

import (
	"net/http"
	"os"
	"path/filepath"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	log "github.com/sirupsen/logrus"
	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"

	_ "github.com/lib/pq"

	database "github.com/Zogwine/Zogwine/internal/database"
	"github.com/Zogwine/Zogwine/internal/handler"
	scraper "github.com/Zogwine/Zogwine/internal/scraper"
	"github.com/Zogwine/Zogwine/internal/status"
)

func main() {
	// setup app runtime status
	status, err := status.New("./config.yml")
	if err != nil {
		log.Fatal(err)
	}

	// setup database
	querier, err := database.Connect(status.Config.Database.Host, status.Config.Database.Port, status.Config.Database.Username, status.Config.Database.Password, status.Config.Database.Database)
	if err != nil {
		log.Fatal(err)
	}
	status.SetDB(querier)

	// setup logger
	log.SetReportCaller(true)
	log.SetOutput(os.Stdout)
	log.SetLevel(log.TraceLevel)
	status.SetLogger(log.New())

	// setup chi
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"https://*", "http://*"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token"},
		ExposedHeaders:   []string{"Link"},
		AllowCredentials: false,
		MaxAge:           300, // Maximum value not ignored by any of major browsers
	}))

	// setup api routes
	api := chi.NewRouter()
	r.Mount("/api", api)
	handler.SetupCore(api, &status)
	handler.SetupUser(api, &status)
	handler.SetupLibrary(api, &status)
	handler.SetupTVS(api, &status)
	handler.SetupMovie(api, &status)
	handler.SetupTag(api, &status)
	handler.SetupPerson(api, &status)
	handler.SetupRole(api, &status)

	r.Get("/api", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("welcome"))
	})

	// static files
	workDir, _ := os.Getwd()
	handler.ServeStatic(r, "/", http.Dir(filepath.Join(workDir, "static")))

	// api doc
	handler.ServeStatic(r, "/swagger", http.Dir(filepath.Join(workDir, "api")))

	// cache
	handler.ServeStatic(r, "/cache", http.Dir(status.Config.Server.CachePath))

	// setup server
	h2s := &http2.Server{}
	server := &http.Server{
		//Addr:    "0.0.0.0:3001",
		Addr:    "127.0.0.1:3001",
		Handler: h2c.NewHandler(r, h2s),
	}

	scraper.Test(status.Log)

	// start !
	log.Fatal(server.ListenAndServe())
}
