package auth

import "github.com/Zogwine/Zogwine/internal/status"

// Function to logout from a session, removes the association between a specific token and a User ID
func Logout(s *status.Status, token string) {
	s.RemoveToken(token)
}

// Function to fully logout a user, removes all the associated tokens to the specified User ID
func LogoutUser(s *status.Status, uid int64) {
	for key, id := range s.ListToken() {
		if id == uid {
			s.RemoveToken(key)
		}
	}
}
