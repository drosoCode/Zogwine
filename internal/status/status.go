package status

import (
	"context"

	"github.com/Zogwine/Zogwine/internal/database"
	log "github.com/sirupsen/logrus"
)

type CtxKey string

// Struct to store user related information
type UserStatus struct {
	// list of groups associated with this user
	UserGroup   []string
	SystemGroup []string
}

// Struct to store global information
type GlobalStatus struct {
	// stores the associations between tokens and user id
	Token map[string]int64
}

type Status struct {
	// stores the app's configuration data
	Config Configuration
	// stores a pointer to the database query instance
	DB *database.Queries
	// stonres a pointer to the logger instance
	Log *log.Logger
	// UserInfo Key for context
	CtxUserKey CtxKey
	// stores the global writable config
	global GlobalStatus
	// stores the user writable config
	user map[int64]UserStatus
}

func New(configPath string) (Status, error) {
	cfg, err := loadConfiguration(configPath)
	if err != nil {
		return Status{}, err
	}

	glb := GlobalStatus{Token: map[string]int64{}}
	return Status{Config: cfg, CtxUserKey: CtxKey("userinfo"), global: glb, user: map[int64]UserStatus{}}, nil
}

func (s *Status) SetDB(q *database.Queries) {
	s.DB = q
}

func (s *Status) SetLogger(l *log.Logger) {
	s.Log = l
}

func (s *Status) NewUser(uid int64) (UserStatus, error) {
	// s.db
	ctx := context.Background()
	ug, err := s.DB.ListGroupFromUser(ctx, database.ListGroupFromUserParams{ID: uid, System: true})
	if err != nil {
		return UserStatus{}, err
	}
	sg, err := s.DB.ListGroupFromUser(ctx, database.ListGroupFromUserParams{ID: uid, System: true})
	if err != nil {
		return UserStatus{}, err
	}
	return UserStatus{UserGroup: ug, SystemGroup: sg}, nil
}

func (s *Status) GetUser(id int64) (UserStatus, error) {
	if val, ok := s.user[id]; ok {
		return val, nil
	}
	user, err := s.NewUser(id)
	if err != nil {
		return UserStatus{}, err
	}
	s.user[id] = user
	return s.user[id], nil
}

func (s *Status) GetGlobal() GlobalStatus {
	return s.global
}

func (s *Status) GetConfig() Configuration {
	return s.Config
}

func (s *Status) SetUser(id int64, u UserStatus) error {
	s.user[id] = u
	return nil
}

func (s *Status) SetGlobal(g GlobalStatus) error {
	s.global = g
	return nil
}
