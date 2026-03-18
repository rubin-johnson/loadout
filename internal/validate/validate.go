package validate

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/coderabbitai/ai-pr-reviewer/internal/manifest"
)

// ValidateBundle validates a bundle directory and returns all validation errors.
// Returns empty slice if valid.
func ValidateBundle(bundleDir string) []string {
	var errors []string

	// Fatal early-return conditions
	if bundleDir == "" {
		return []string{"bundle directory path cannot be empty"}
	}

	// Check if path exists
	info, err := os.Stat(bundleDir)
	if err != nil {
		if os.IsNotExist(err) {
			return []string{fmt.Sprintf("bundle directory does not exist: %s", bundleDir)}
		}
		return []string{fmt.Sprintf("error accessing bundle directory: %v", err)}
	}

	// Check if it's a directory
	if !info.IsDir() {
		return []string{fmt.Sprintf("path is not a directory: %s", bundleDir)}
	}

	// Check if manifest.yaml exists
	manifestPath := filepath.Join(bundleDir, "manifest.yaml")
	if _, err := os.Stat(manifestPath); err != nil {
		if os.IsNotExist(err) {
			return []string{"manifest.yaml not found in bundle directory"}
		}
		return []string{fmt.Sprintf("error accessing manifest.yaml: %v", err)}
	}

	// Delegate YAML and field validation to manifest.Load
	m, err := manifest.Load(bundleDir)
	if err != nil {
		errors = append(errors, err.Error())
		return errors // If manifest loading fails, no point checking targets
	}

	// Check each declared target path exists on disk
	for _, target := range m.Targets {
		targetPath := filepath.Join(bundleDir, target.Path)
		if _, err := os.Stat(targetPath); err != nil {
			if os.IsNotExist(err) {
				errors = append(errors, fmt.Sprintf("target file does not exist: %s", target.Path))
			} else {
				errors = append(errors, fmt.Sprintf("error accessing target file %s: %v", target.Path, err))
			}
		}
	}

	return errors
}
