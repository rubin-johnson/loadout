package capture

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"

	"github.com/cline/loadout/internal/secrets"
)

// DEFAULT_CAPTURES defines the files and directories to capture
var DEFAULT_CAPTURES = []string{
	"CLAUDE.md",
	".cursor/rules",
	".vscode",
	"docs",
	"scripts",
	"config",
	"*.md",
	"*.txt",
	"*.json",
	"*.yaml",
	"*.yml",
	"*.toml",
	"Dockerfile*",
	"docker-compose*",
	"Makefile",
	"requirements*.txt",
	"package*.json",
	"go.mod",
	"go.sum",
	"Cargo.toml",
	"Cargo.lock",
}

// SCAN_DIRS defines directories to scan for secrets
var SCAN_DIRS = []string{
	"config",
	"scripts",
	".env*",
	"secrets",
	"keys",
}

// Manifest represents the bundle manifest structure
type Manifest struct {
	Version     string            `yaml:"version"`
	CreatedAt   string            `yaml:"created_at"`
	SourceDir   string            `yaml:"source_dir"`
	Captured    []string          `yaml:"captured"`
	Metadata    map[string]string `yaml:"metadata,omitempty"`
}

// isDBFile checks if a filename is a database file that should be skipped
func isDBFile(name string) bool {
	return strings.HasSuffix(strings.ToLower(name), ".db")
}

// CaptureBundle snapshots a source directory as a loadout bundle
func CaptureBundle(sourceDir, outputDir string, overwrite bool) error {
	// Check if output directory exists
	if _, err := os.Stat(outputDir); err == nil && !overwrite {
		return fmt.Errorf("output directory %s already exists and overwrite is false", outputDir)
	}

	// Create output directory
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	var captured []string
	var hasTargets bool

	// Walk through source directory and copy matching files
	err := filepath.WalkDir(sourceDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		// Skip database files
		if isDBFile(d.Name()) {
			return nil
		}

		// Get relative path from source
		relPath, err := filepath.Rel(sourceDir, path)
		if err != nil {
			return err
		}

		// Skip root directory
		if relPath == "." {
			return nil
		}

		// Check if this path matches any capture pattern
		if shouldCapture(relPath, d.IsDir()) {
			destPath := filepath.Join(outputDir, relPath)

			if d.IsDir() {
				// Create directory
				if err := os.MkdirAll(destPath, 0755); err != nil {
					return fmt.Errorf("failed to create directory %s: %w", destPath, err)
				}
			} else {
				// Copy file
				if err := copyFile(path, destPath); err != nil {
					return fmt.Errorf("failed to copy file %s: %w", path, err)
				}
				captured = append(captured, relPath)
				hasTargets = true
			}
		}

		return nil
	})

	if err != nil {
		return fmt.Errorf("failed to walk source directory: %w", err)
	}

	// Scan for secrets in specified directories
	for _, scanDir := range SCAN_DIRS {
		scanPath := filepath.Join(sourceDir, scanDir)
		if _, err := os.Stat(scanPath); err == nil {
			if warnings := secrets.ScanForSecrets(scanPath); len(warnings) > 0 {
				for _, warning := range warnings {
					fmt.Fprintf(os.Stderr, "WARNING: %s\n", warning)
				}
			}
		}
	}

	// Generate stub CLAUDE.md if no targets were captured
	if !hasTargets {
		claudePath := filepath.Join(outputDir, "CLAUDE.md")
		stubContent := "# Loadout Bundle\n\nThis bundle was generated from an empty or unmatched source directory.\n\n## Contents\n\nNo matching files were found to capture.\n"
		if err := os.WriteFile(claudePath, []byte(stubContent), 0644); err != nil {
			return fmt.Errorf("failed to create stub CLAUDE.md: %w", err)
		}
		captured = append(captured, "CLAUDE.md")
	}

	// Create manifest
	manifest := Manifest{
		Version:   "1.0",
		CreatedAt: "2024-01-01T00:00:00Z", // TODO: use actual timestamp
		SourceDir: sourceDir,
		Captured:  captured,
	}

	// Write manifest.yaml
	manifestPath := filepath.Join(outputDir, "manifest.yaml")
	manifestData, err := yaml.Marshal(manifest)
	if err != nil {
		return fmt.Errorf("failed to marshal manifest: %w", err)
	}

	if err := os.WriteFile(manifestPath, manifestData, 0644); err != nil {
		return fmt.Errorf("failed to write manifest: %w", err)
	}

	return nil
}

// shouldCapture checks if a path matches any capture pattern
func shouldCapture(path string, isDir bool) bool {
	for _, pattern := range DEFAULT_CAPTURES {
		// Direct match
		if path == pattern {
			return true
		}

		// Glob pattern match
		if matched, _ := filepath.Match(pattern, filepath.Base(path)); matched {
			return true
		}

		// Directory prefix match
		if isDir && strings.HasPrefix(path, pattern+"/") {
			return true
		}
	}
	return false
}

// copyFile copies a file from src to dst
func copyFile(src, dst string) error {
	// Create destination directory if needed
	if err := os.MkdirAll(filepath.Dir(dst), 0755); err != nil {
		return err
	}

	// Read source file
	srcData, err := os.ReadFile(src)
	if err != nil {
		return err
	}

	// Write destination file
	return os.WriteFile(dst, srcData, 0644)
}
