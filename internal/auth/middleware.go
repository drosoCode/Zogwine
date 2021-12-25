package auth

import (
	"context"
	"net/http"

	"github.com/Zogwine/Zogwine/internal/status"
	"github.com/Zogwine/Zogwine/internal/util/srv"
)

type UserInfo struct {
	Token string
	ID    int64
}

// check user authentication and authorization and add user id/token to the request context
func CheckUserMiddleware(s *status.Status, groups ...string) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		fn := func(w http.ResponseWriter, r *http.Request) {
			// get user token from request
			token, err := GetToken(r)
			if srv.IfError(w, r, err) {
				return
			}
			// get user id from token
			uid, err := GetUserID(s, token)
			if srv.IfError(w, r, err) {
				return
			}
			// check user groups
			for _, g := range groups {
				ok := CheckGroup(s, uid, g, true)
				if !ok {
					srv.Error(w, r, 400, "user not in group: "+g)
					return
				}
			}
			// if all ok, add token and userid to context and continue
			r = r.WithContext(context.WithValue(r.Context(), s.CtxUserKey, UserInfo{Token: token, ID: uid}))
			next.ServeHTTP(w, r)
		}
		return http.HandlerFunc(fn)
	}
}
