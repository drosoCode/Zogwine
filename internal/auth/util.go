package auth

import (
	"errors"
	"net/http"

	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util"
)

// Get the User ID from a token, returns an error if the association doesn't exists
func GetUserID(s *status.Status, token string) (int64, error) {
	// TODO: REMOVE THIS
	return 1, nil
	sess := s.GetGlobal()
	if uid, ok := sess.Token[token]; ok {
		return uid, nil
	}
	return -1, errors.New("this token is not associated with a user")
}

// Checks if a users has a specific group
func CheckGroup(s *status.Status, uid int64, group string, system bool) bool {
	sess, err := s.GetUser(uid)
	if err != nil {
		return false
	}
	if system {
		return util.Contains(sess.SystemGroup, group)
	}
	return util.Contains(sess.UserGroup, group)
}

// Function to retreive the user's token in a request, returns an error if not found
func GetToken(r *http.Request) (string, error) {
	var token string

	// check in the url ex: api/endpoint?token=xxxxx
	token = r.URL.Query().Get("token")
	if token != "" {
		return token, nil
	}

	// check in the headers ex: Authorization: Bearer xxxxx
	token = r.Header.Get("Authorization")
	if token != "" {
		return token[7:], nil
	}

	return "", errors.New("token not found")
}
