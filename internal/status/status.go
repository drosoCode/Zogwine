package status

import (
	"context"
	"encoding/json"
	"io/ioutil"

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

type TaskStatus int

const (
	TaskStopped TaskStatus = 0 // stopped
	TaskRunning TaskStatus = 1 // running
	TaskError   TaskStatus = 2 // exited with an error
)

type TranscodeTaskStatus struct {
	MediaType database.MediaType
	MediaData int64
	Selector  int64
}

// Struct to store global information
type GlobalStatus struct {
	// stores the associations between tokens and user id
	Token map[string]int64 `json:"token"`
	// List of running tasks
	task map[string]TaskStatus
	// List of running transcoding tasks
	transcodeTask map[string]TranscodeTaskStatus
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

type JsonStatus struct {
	Global GlobalStatus `json:"global"`
	// User   map[int64]UserStatus `json:"user"`
}

func New(configPath string) (Status, error) {
	cfg, err := loadConfiguration(configPath)
	if err != nil {
		return Status{}, err
	}

	status := map[string]TaskStatus{
		"cache": TaskStopped,
	}
	glb := GlobalStatus{Token: map[string]int64{}, task: status, transcodeTask: map[string]TranscodeTaskStatus{}}
	usr := map[int64]UserStatus{}

	if cfg.Server.PersistData != "" {
		jdata, err := ioutil.ReadFile(cfg.Server.PersistData)
		if err == nil {
			var back JsonStatus
			err = json.Unmarshal(jdata, &back)
			if err == nil {
				glb.Token = back.Global.Token
				// usr = back.User
			}
		}
	}

	return Status{Config: cfg, CtxUserKey: CtxKey("userinfo"), global: glb, user: usr}, nil
}

func (s *Status) persistData() {
	if s.Config.Server.PersistData == "" {
		return
	}
	s.Log.Info("persisting data ...")
	// data := JsonStatus{Global: s.global, User: s.user}
	data := JsonStatus{Global: s.global}
	jdata, err := json.Marshal(data)
	if err != nil {
		s.Log.Errorf("error while persisting data: %s", err)
	}
	err = ioutil.WriteFile(s.Config.Server.PersistData, jdata, 0644)
	if err != nil {
		s.Log.Errorf("error while persisting data: %s", err)
	}
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

func (s *Status) getUser(id int64) (UserStatus, error) {
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

func (s *Status) SetToken(token string, uid int64) error {
	s.global.Token[token] = uid
	s.persistData()
	return nil
}

func (s *Status) RemoveToken(token string) error {
	delete(s.global.Token, token)
	s.persistData()
	return nil
}

func (s *Status) ListToken() map[string]int64 {
	return s.global.Token
}

func (s *Status) SetTask(name string, task TaskStatus) error {
	s.global.task[name] = task
	return nil
}

func (s *Status) RemoveTask(name string) error {
	delete(s.global.task, name)
	return nil
}

func (s *Status) ListTask() map[string]TaskStatus {
	return s.global.task
}

func (s *Status) SetTranscodeTask(name string, task TranscodeTaskStatus) error {
	s.global.transcodeTask[name] = task
	s.persistData()
	return nil
}

func (s *Status) RemoveTranscodeTask(name string) error {
	delete(s.global.transcodeTask, name)
	s.persistData()
	return nil
}

func (s *Status) ListTranscodeTask() map[string]TranscodeTaskStatus {
	return s.global.transcodeTask
}

func (s *Status) ListUserGroup(uid int64) []string {
	user, err := s.getUser(uid)
	if err != nil {
		return make([]string, 0)
	}
	return user.UserGroup
}

func (s *Status) ListUserSystemGroup(uid int64) []string {
	user, err := s.getUser(uid)
	if err != nil {
		return make([]string, 0)
	}
	return user.SystemGroup
}
