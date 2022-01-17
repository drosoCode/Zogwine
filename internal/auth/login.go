package auth

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"net"
	"net/http"

	"github.com/Zogwine/Zogwine/internal/status"
	"golang.org/x/crypto/bcrypt"
)

// Generate a random token
func generateToken() string {
	bytes := make([]byte, 32)
	rand.Read(bytes)
	return hex.EncodeToString(bytes)
}

// JSON body expected for user authentication
type authPacket struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// Function to authenticate the user, either through internal user/password auth or through header auth
func Authenticate(r *http.Request, s *status.Status) (int64, error) {
	// internal auth mode, uses the database and the credentials in the post body
	if s.Config.Authentication.Mode == "internal" {
		auth := authPacket{}
		err := json.NewDecoder(r.Body).Decode(&auth)

		// password is generated with:
		// bytes, err := bcrypt.GenerateFromPassword([]byte(password), 14)
		if err != nil {
			return -1, err
		}
		ctx := context.Background()
		userData, err := s.DB.GetUserLoginFromUsername(ctx, auth.Username)
		if err != nil {
			return -1, err
		}
		if bcrypt.CompareHashAndPassword([]byte(userData.Password), []byte(auth.Password)) == nil {
			return userData.ID, nil
		}
		return -1, errors.New("unauthorized")

		// header auth mode, uses the provided headers to map a username in the header to a user stored in database
	} else if s.Config.Authentication.Mode == "header" {
		source := net.ParseIP(r.RemoteAddr)
		proxies := s.Config.Authentication.Header.TrustedProxies
		authorizedSource := false
		for _, p := range proxies {
			_, ipnet, err := net.ParseCIDR(p)
			if err == nil && ipnet.Contains(source) {
				authorizedSource = true
				break
			}
		}

		if !authorizedSource {
			return -1, errors.New("source is not authorized to send authentication headers")
		}

		username := r.Header.Get(s.Config.Authentication.Header.UserHeader)
		ctx := context.Background()
		userData, err := s.DB.GetUserLoginFromUsername(ctx, username)
		if err != nil {
			// TODO: Auto Register ?
			return -1, err
		}
		return userData.ID, nil
	}

	return -1, errors.New("invalid authentication mode")
}

// Function to grant access to a user, associates a User ID to a token and returns this token
func Login(s *status.Status, uid int64) string {
	token := generateToken()
	s.SetToken(token, uid)
	return token
}
