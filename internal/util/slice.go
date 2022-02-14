package util

func Contains[T comparable](slice []T, elem T) bool {
	for _, x := range slice {
		if x == elem {
			return true
		}
	}
	return false
}
