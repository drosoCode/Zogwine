package util

func Contains[T comparable](slice []T, elem T) bool {
	for _, x := range slice {
		if x == elem {
			return true
		}
	}
	return false
}

func Index[T comparable](slice []T, elem T) int {
	for i, x := range slice {
		if x == elem {
			return i
		}
	}
	return -1
}
