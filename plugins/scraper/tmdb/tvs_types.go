package tmdb

type TMDBTVSearch struct {
	Page         int `json:"page"`
	TotalPages   int `json:"total_pages"`
	TotalResults int `json:"total_results"`
	Results      []struct {
		PosterPath       string   `json:"poster_path"`
		Popularity       float64  `json:"popularity"`
		ID               int      `json:"id"`
		BackdropPath     string   `json:"backdrop_path"`
		VoteAverage      float64  `json:"vote_average"`
		Overview         string   `json:"overview"`
		FirstAirDate     string   `json:"first_air_date"`
		OriginCountry    []string `json:"origin_country"`
		GenreIDS         []int    `json:"genre_ids"`
		OriginalLanguage string   `json:"original_language"`
		VoteCount        int      `json:"vote_count"`
		Name             string   `json:"name"`
		OriginalName     string   `json:"original_name"`
	} `json:"results"`
}

type TMDBEpisodeGroup struct {
	Results []struct {
		Description  string `json:"description"`
		EpisodeCount int    `json:"episode_count"`
		GroupCount   int    `json:"group_count"`
		ID           string `json:"id"`
		Name         string `json:"name"`
		Network      struct {
			ID            int    `json:"id"`
			LogoPath      string `json:"logo_path"`
			Name          string `json:"name"`
			OriginCountry string `json:"origin_country"`
		} `json:"network"`
		Type int `json:"type"`
	}
	ID int `json:"id"`
}

type TMDBTVShow struct {
	BackdropPath string `json:"backdrop_path"`
	CreatedBy    []struct {
		ID          int    `json:"id"`
		CreditID    string `json:"credit_id"`
		Name        string `json:"name"`
		Gender      int    `json:"gender"`
		ProfilePath string `json:"profile_path"`
	} `json:"created_by"`
	EpisodeRunTime []int  `json:"episode_run_time"`
	FirstAirDate   string `json:"first_air_date"`
	Genres         []struct {
		ID   int    `json:"id"`
		Name string `json:"name"`
	} `json:"genres"`
	Homepage         string   `json:"homepage"`
	ID               int      `json:"id"`
	InProduction     bool     `json:"in_production"`
	Languages        []string `json:"languages"`
	LastAirDate      string   `json:"last_air_date"`
	LastEpisodeToAir struct {
		AirDate        string  `json:"air_date"`
		EpisodeNumber  int     `json:"episode_number"`
		ID             int     `json:"id"`
		Name           string  `json:"name"`
		Overview       string  `json:"overview"`
		ProductionCode string  `json:"production_code"`
		SeasonNumber   int     `json:"season_number"`
		StillPath      string  `json:"still_path"`
		VoteAverage    float64 `json:"vote_average"`
		VoteCount      int     `json:"vote_count"`
	} `json:"last_episode_to_air"`
	Name             string `json:"name"`
	NextEpisodeToAir struct {
		AirDate        string `json:"air_date"`
		EpisodeNumber  int    `json:"episode_number"`
		ID             int    `json:"id"`
		Name           string `json:"name"`
		Overview       string `json:"overview"`
		ProductionCode string `json:"production_code"`
		SeasonNumber   int    `json:"season_number"`
		StillPath      string `json:"still_path"`
	} `json:"next_episode_to_air"`
	Networks []struct {
		Name          string `json:"name"`
		ID            int    `json:"id"`
		LogoPath      string `json:"logo_path"`
		OriginCountry string `json:"origin_country"`
	} `json:"networks"`
	NumberOfEpisodes    int      `json:"number_of_episodes"`
	NumberOfSeasons     int      `json:"number_of_seasons"`
	OriginCountry       []string `json:"origin_country"`
	OriginLanguage      string   `json:"origin_language"`
	OriginalName        string   `json:"original_name"`
	Overview            string   `json:"overview"`
	Popularity          float64  `json:"popularity"`
	PosterPath          string   `json:"poster_path"`
	ProductionCompanies []struct {
		Name          string `json:"name"`
		ID            int    `json:"id"`
		LogoPath      string `json:"logo_path"`
		OriginCountry string `json:"origin_country"`
	} `json:"production_companies"`
	ProductionCountries []struct {
		ISO31661 string `json:"iso_3166_1"`
		Name     string `json:"name"`
	} `json:"production_countries"`
	Seasons []struct {
		ID           int    `json:"id"`
		Name         string `json:"name"`
		AirDate      string `json:"air_date"`
		EpisodeCount int    `json:"episode_count"`
		Overview     string `json:"overview"`
		PosterPath   string `json:"poster_path"`
		SeasonNumber int    `json:"season_number"`
	} `json:"seasons"`
	SpokenLanguages []struct {
		ISO6391     string `json:"iso_639_1"`
		Name        string `json:"name"`
		EnglishName string `json:"english_name"`
	} `json:"spoken_languages"`
	Status      string  `json:"status"`
	TagLine     string  `json:"tagline"`
	Type        string  `json:"type"`
	VoteAverage float64 `json:"vote_average"`
	VoteCount   int     `json:"vote_count"`
}

// get tvs season

type TMDBSeason struct {
	ID_          string `json:"_id"`
	ID           int    `json:"id"`
	AirDate      string `json:"air_date"`
	Name         string `json:"name"`
	Overview     string `json:"overview"`
	PosterPath   string `json:"poster_path"`
	SeasonNumber int    `json:"season_number"`
	Episodes     []struct {
		AirDate       string `json:"air_date"`
		EpisodeNumber int    `json:"episode_number"`
		Crew          []struct {
			Department         string  `json:"department"`
			Job                string  `json:"job"`
			CreditID           string  `json:"credit_id"`
			Adult              bool    `json:"adult"`
			Gender             int     `json:"gender"`
			ID                 int     `json:"id"`
			KnownForDepartment string  `json:"known_for_department"`
			Name               string  `json:"name"`
			OriginalName       string  `json:"original_name"`
			Popularity         float64 `json:"popularity"`
			ProfilePath        string  `json:"profile_path"`
		} `json:"crew"`
		GuestStars []struct {
			Department         string  `json:"department"`
			Job                string  `json:"job"`
			CreditID           string  `json:"credit_id"`
			Adult              bool    `json:"adult"`
			Gender             int     `json:"gender"`
			ID                 int     `json:"id"`
			KnownForDepartment string  `json:"known_for_department"`
			Name               string  `json:"name"`
			OriginalName       string  `json:"original_name"`
			Popularity         float64 `json:"popularity"`
			ProfilePath        string  `json:"profile_path"`
		} `json:"guest_stars"`
		ID             int     `json:"id"`
		Name           string  `json:"name"`
		Overview       string  `json:"overview"`
		ProductionCode string  `json:"production_code"`
		SeasonNumber   int     `json:"season_number"`
		VoteAverage    float64 `json:"vote_average"`
		VoteCount      int     `json:"vote_count"`
	} `json:"episodes"`
}

type TMDBEpisode struct {
	AirDate string `json:"air_date"`
	Crew    []struct {
		ID          int    `json:"id"`
		CreditID    string `json:"credit_id"`
		Name        string `json:"name"`
		Department  string `json:"department"`
		Job         string `json:"job"`
		ProfilePath string `json:"profile_path"`
	} `json:"crew"`
	EpisodeNumber int `json:"episode_number"`
	GuestStars    []struct {
		ID          int    `json:"id"`
		CreditID    string `json:"credit_id"`
		Name        string `json:"name"`
		ProfilePath string `json:"profile_path"`
		Character   string `json:"character"`
		Order       int    `json:"order"`
	} `json:"guest_stars"`
	Name           string  `json:"name"`
	Overview       string  `json:"overview"`
	ID             int     `json:"id"`
	ProductionCode string  `json:"production_code"`
	SeasonNumber   int     `json:"season_number"`
	StillPath      string  `json:"still_path"`
	VoteAverage    float64 `json:"vote_average"`
	VoteCount      int     `json:"vote_count"`
}

type TMDBEpisodeGroupData struct {
	Description  string `json:"description"`
	EpisodeCount int    `json:"episode_count"`
	GroupCount   int    `json:"group_count"`
	ID           string `json:"id"`
	Name         string `json:"name"`
	Network      struct {
		ID            int    `json:"id"`
		LogoPath      string `json:"logo_path"`
		Name          string `json:"name"`
		OriginCountry string `json:"origin_country"`
	} `json:"network"`
	Type   int `json:"type"`
	Groups []struct {
		ID       string        `json:"id"`
		Name     string        `json:"name"`
		Order    int           `json:"order"`
		Locked   bool          `json:"locked"`
		Episodes []TMDBEpisode `json:"episodes"`
	} `json:"groups"`
}

type TMDBTVSCredits struct {
	Cast []struct {
		Adult              bool    `json:"adult"`
		Gender             int     `json:"gender"`
		ID                 int     `json:"id"`
		KnownForDepartment string  `json:"known_for_department"`
		Name               string  `json:"name"`
		OriginalName       string  `json:"original_name"`
		Popularity         float64 `json:"popularity"`
		Character          string  `json:"character"`
		CreditID           string  `json:"credit_id"`
		Order              int     `json:"order"`
	} `json:"cast"`
	Crew []struct {
		Adult              bool    `json:"adult"`
		Gender             int     `json:"gender"`
		ID                 int     `json:"id"`
		KnownForDepartment string  `json:"known_for_department"`
		Name               string  `json:"name"`
		OriginalName       string  `json:"original_name"`
		Popularity         float64 `json:"popularity"`
		ProfilePath        string  `json:"profile_path"`
		CreditID           string  `json:"credit_id"`
		Department         string  `json:"department"`
		Job                string  `json:"job"`
	} `json:"crew"`
}
