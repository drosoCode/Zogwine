package tmdb

type TMDBPersonSearch struct {
	Page         int `json:"page"`
	TotalPages   int `json:"total_pages"`
	TotalResults int `json:"total_results"`
	Results      []struct {
		ProfilePath string                 `json:"profile_path"`
		Adult       bool                   `json:"adult"`
		ID          int                    `json:"id"`
		Name        string                 `json:"name"`
		Popularity  float64                `json:"popularity"`
		KnownFor    map[string]interface{} `json:"known_for"`
	} `json:"results"`
}

type TMDBPersonData struct {
	Birthday           string   `json:"birthday"`
	KnownForDepartment string   `json:"known_for_department"`
	Deathday           string   `json:"deathday"`
	ID                 int      `json:"id"`
	Name               string   `json:"name"`
	AlsoKnownAs        []string `json:"also_known_as"`
	Gender             int      `json:"gender"`
	Biography          string   `json:"biography"`
	Popularity         float64  `json:"popularity"`
	PlaceOfBirth       string   `json:"place_of_birth"`
	ProfilePath        string   `json:"profile_path"`
	Adult              bool     `json:"adult"`
	IMDBID             string   `json:"imdb_id"`
	Homepage           string   `json:"homepage"`
}
