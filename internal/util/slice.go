package util

func Contains[T int64 | float64 | string](slice []T, elem T) bool {
	for _, x := range slice {
		if x == elem {
			return true
		}
	}
	return false
}
