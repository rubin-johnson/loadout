package validate

import (
	"fmt"
	"os"
	"path/filepath"

	"bundle-tool/internal/manifest"
)

// ValidateBundle validates a bundle directory and returns all validation errors.
// Returns empty slice if bundle is valid.
func ValidateBundle(bundleDir string) []string {
	var errors []string

	// Fatal early-return conditions
	if bundleDir == "" {
		errors = append(errors, "bundle directory path cannot be empty")
		return errors
	}

	// Check if path exists
	if _, err := os.Stat(bundleDir); os.IsNotExist(err) {
		errors = append(errors, fmt.Sprintf("bundle directory does not exist: %s", bundleDir))
		return errors
	}

	// Check if it's a directory
	if info, err := os.Stat(bundleDir); err == nil && !info.IsDir() {
		errors = append(errors, fmt.Sprintf("path is not a directory: %s", bundleDir))
		return errors
	}

	// Check if manifest.yaml exists
	manifestPath := filepath.Join(bundleDir, "manifest.yaml")
	if _, err := os.Stat(manifestPath); os.IsNotExist(err) {
		errors = append(errors, "manifest.yaml not found in bundle directory")
		return errors
	}

	// Delegate to manifest.Load for YAML and field validation
	m, err := manifest.Load(manifestPath)
	if err != nil {
		errors = append(errors, err.Error())
		return errors
	}

	// Check each declared target path exists on disk
	for _, target := range m.Targets {
		targetPath := filepath.Join(bundleDir, target.Path)
		if _, err := os.Stat(targetPath); os.IsNotExist(err) {
			errors = append(errors, fmt.Sprintf("target file does not exist: %s", target.Path))
		}
	}

	return errors
}
