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
	userGroup   []string
	systemGroup []string
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
	token map[string]int64
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

func New(configPath string) (Status, error) {
	cfg, err := loadConfiguration(configPath)
	if err != nil {
		return Status{}, err
	}

	glb := GlobalStatus{token: map[string]int64{}, task: map[string]TaskStatus{}, transcodeTask: map[string]TranscodeTaskStatus{}}
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
	return UserStatus{userGroup: ug, systemGroup: sg}, nil
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

func (s *Status) persistData() {
	s.Log.Debug("persisting data ...")
}

func (s *Status) SetToken(token string, uid int64) error {
	s.global.token[token] = uid
	s.persistData()
	return nil
}

func (s *Status) RemoveToken(token string) error {
	delete(s.global.token, token)
	s.persistData()
	return nil
}

func (s *Status) ListToken() map[string]int64 {
	return s.global.token
}

func (s *Status) SetTask(name string, task TaskStatus) error {
	s.global.task[name] = task
	s.persistData()
	return nil
}

func (s *Status) RemoveTask(name string) error {
	delete(s.global.task, name)
	s.persistData()
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
	return user.userGroup
}

func (s *Status) ListUserSystemGroup(uid int64) []string {
	user, err := s.getUser(uid)
	if err != nil {
		return make([]string, 0)
	}
	return user.systemGroup
}
