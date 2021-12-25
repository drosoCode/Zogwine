package status

import (
	"os"

	"gopkg.in/yaml.v2"
)

type Configuration struct {
	// database connection settings
	Database struct {
		Host     string `yaml:"host"`
		Port     int    `yaml:"port"`
		Username string `yaml:"username"`
		Password string `yaml:"password"`
		Database string `yaml:"database"`
	} `yaml:"database,flow"`
	// encoding settings
	Encoding struct {
		// list of the supported encoders, sorted from the best to the worse
		Encoders []string `yaml:"encoders,flow"`
		// duration of each chunk in a HLS strem
		HLSDuration int64 `yaml:"hls_duration"`
		// encoder timeout (in sec), after this, the system will attempt to kill and restart the transcoder
		Timeout int64 `yaml:"timeout"`
		// Constant Rate Factor for H264 encoding
		CRF int64 `yaml:"crf"`
	} `yaml:"encoding,flow"`
	Files struct {
		// list of the supported extensions for video files
		VideoFiles []string `yaml:"video_files,flow"`
	} `yaml:"files,flow"`
	Authentication struct {
		// mode of authentication: 0 (internal) or 1 (header)
		Mode string `yaml:"mode"`
		// if header authentication is used
		Header struct {
			UserHeader        string            `yaml:"username_header"`                // name of the header that contains the username used to login
			NameHeader        string            `yaml:"name_header"`                    // name of the header that contains the user friendly name
			GroupHeader       string            `yaml:"group_header"`                   // name of the header that contains the user groups
			GroupMap          map[string]string `yaml:"group_map,flow"`                 // hashmap used to map some header group name to this system (ex: header ZOGWINE_ADMIN can be mapped to system group ADMIN)
			AutoRegister      bool              `yaml:"auto_register"`                  // if a user can be automatically registered
			AutoRegisterGroup string            `yaml:"auto_register_header,omitempty"` // a group name that needs to be specified to enable auto registration, leave empty to disable this filter
			TrustedProxies    []string          `yaml:"trusted_proxies,flow"`           // ip of the proxies authorized to send these headers
		} `yaml:"header,flow,omitempty"`
	}
	Server struct {
		BaseURL   string `yaml:"base_url"`   // url used to access the Zogwine instance
		CachePath string `yaml:"cache_path"` // path to the cache folder
		LogPath   string `yaml:"log_path"`   // path to the logs folder
		LogLevel  string `yaml:"log_level"`  // the log level
	} `yaml:"server,flow"`
}

func loadConfiguration(path string) (Configuration, error) {
	config := Configuration{}
	file, err := os.ReadFile(path)
	if err != nil {
		return config, err
	}
	return config, yaml.Unmarshal(file, &config)
}
