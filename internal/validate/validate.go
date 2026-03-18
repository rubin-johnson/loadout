package validate

import (
	"os"
	"path/filepath"

	"github.com/rubin-johnson/loadout/internal/manifest"
)

// ValidateBundle validates a bundle directory and returns all validation errors
// Returns empty slice if bundle is valid
func ValidateBundle(bundleDir string) []string {
	var errors []string

	// Fatal early-return conditions
	if bundleDir == "" {
		errors = append(errors, "bundle directory path cannot be empty")
		return errors
	}

	// Check if path exists
	info, err := os.Stat(bundleDir)
	if err != nil {
		if os.IsNotExist(err) {
			errors = append(errors, "bundle directory does not exist")
		} else {
			errors = append(errors, "cannot access bundle directory: "+err.Error())
		}
		return errors
	}

	// Check if it's a directory
	if !info.IsDir() {
		errors = append(errors, "path is not a directory")
		return errors
	}

	// Check if manifest.yaml exists
	manifestPath := filepath.Join(bundleDir, "manifest.yaml")
	if _, err := os.Stat(manifestPath); err != nil {
		if os.IsNotExist(err) {
			errors = append(errors, "manifest.yaml not found")
		} else {
			errors = append(errors, "cannot access manifest.yaml: "+err.Error())
		}
		return errors
	}

	// Delegate YAML parsing and field validation to manifest.Load
	m, err := manifest.Load(bundleDir)
	if err != nil {
		errors = append(errors, err.Error())
		return errors
	}

	// Check that each declared target path exists on disk
	for _, target := range m.Targets {
		targetPath := filepath.Join(bundleDir, target.Path)
		if _, err := os.Stat(targetPath); err != nil {
			if os.IsNotExist(err) {
				errors = append(errors, "target file does not exist: "+target.Path)
			} else {
				errors = append(errors, "cannot access target file "+target.Path+": "+err.Error())
			}
		}
	}

	return errors
}
