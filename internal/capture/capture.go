package capture

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"

	"loadout-system/internal/secrets"
)

// DEFAULT_CAPTURES maps file patterns to their descriptions
var DEFAULT_CAPTURES = map[string]string{
	"CLAUDE.md":       "Claude configuration and context",
	".cursor/rules/*": "Cursor IDE rules and settings",
	".vscode/*":       "VS Code settings and extensions",
	"*.code-workspace": "VS Code workspace files",
	".env.example":    "Environment variable templates",
	"docker-compose*.yml": "Docker composition files",
	"Dockerfile*":     "Docker build files",
	"Makefile":        "Build automation",
	"package.json":    "Node.js dependencies",
	"requirements.txt": "Python dependencies",
	"go.mod":          "Go module definition",
	"go.sum":          "Go module checksums",
	"Cargo.toml":      "Rust dependencies",
	"pyproject.toml":  "Python project configuration",
	"*.yaml":          "YAML configuration files",
	"*.yml":           "YAML configuration files",
	"*.toml":          "TOML configuration files",
	"*.json":          "JSON configuration files",
	"README*":         "Project documentation",
	"LICENSE*":        "License files",
	".gitignore":      "Git ignore patterns",
	".gitattributes":  "Git attributes",
}

// SCAN_DIRS lists directories to scan for secrets
var SCAN_DIRS = []string{
	".",
	"config",
	"configs",
	"env",
	".env",
	"secrets",
	"keys",
	"certs",
	"ssl",
}

// isDBFile returns true if the filename has a database extension
func isDBFile(name string) bool {
	return strings.HasSuffix(strings.ToLower(name), ".db")
}

// Manifest represents the bundle manifest structure
type Manifest struct {
	Version     string            `yaml:"version"`
	CreatedAt   string            `yaml:"created_at"`
	SourceDir   string            `yaml:"source_dir"`
	CapturedFiles []string        `yaml:"captured_files"`
	Captures    map[string]string `yaml:"captures"`
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

	// Scan for secrets in specified directories
	for _, dir := range SCAN_DIRS {
		scanPath := filepath.Join(sourceDir, dir)
		if _, err := os.Stat(scanPath); err == nil {
			if warnings := secrets.ScanForSecrets(scanPath); len(warnings) > 0 {
				for _, warning := range warnings {
					fmt.Fprintf(os.Stderr, "WARNING: %s\n", warning)
				}
			}
		}
	}

	// Track captured files
	var capturedFiles []string
	hasTargets := false

	// Walk through source directory and copy matching files
	err := filepath.WalkDir(sourceDir, func(path string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		// Skip database files
		if !entry.IsDir() && isDBFile(entry.Name()) {
			return nil
		}

		// Get relative path from source directory
		relPath, err := filepath.Rel(sourceDir, path)
		if err != nil {
			return err
		}

		// Skip the root directory itself
		if relPath == "." {
			return nil
		}

		// Check if this file/directory matches any capture pattern
		matched := false
		for pattern := range DEFAULT_CAPTURES {
			if matchPattern(relPath, pattern) {
				matched = true
				break
			}
		}

		if matched {
			hasTargets = true
			destPath := filepath.Join(outputDir, relPath)

			if entry.IsDir() {
				// Create directory
				if err := os.MkdirAll(destPath, entry.Type().Perm()); err != nil {
					return fmt.Errorf("failed to create directory %s: %w", destPath, err)
				}
			} else {
				// Copy file
				if err := copyFile(path, destPath); err != nil {
					return fmt.Errorf("failed to copy file %s: %w", path, err)
				}
				capturedFiles = append(capturedFiles, relPath)
			}
		}

		return nil
	})

	if err != nil {
		return fmt.Errorf("failed to walk source directory: %w", err)
	}

	// Generate stub CLAUDE.md if no targets were captured
	if !hasTargets {
		claudeContent := "# Claude Configuration\n\nThis bundle was created from a directory with no recognized configuration files.\n\n## Captured Files\n\nNo files matched the default capture patterns.\n"
		claudePath := filepath.Join(outputDir, "CLAUDE.md")
		if err := os.WriteFile(claudePath, []byte(claudeContent), 0644); err != nil {
			return fmt.Errorf("failed to create stub CLAUDE.md: %w", err)
		}
		capturedFiles = append(capturedFiles, "CLAUDE.md")
	}

	// Create manifest
	manifest := Manifest{
		Version:       "1.0",
		CreatedAt:     "2026-03-18", // Using current date from user_info
		SourceDir:     sourceDir,
		CapturedFiles: capturedFiles,
		Captures:      DEFAULT_CAPTURES,
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

// matchPattern checks if a file path matches a capture pattern
func matchPattern(path, pattern string) bool {
	// Handle glob patterns
	if strings.Contains(pattern, "*") {
		matched, _ := filepath.Match(pattern, path)
		return matched
	}
	
	// Handle directory patterns (ending with /*)
	if strings.HasSuffix(pattern, "/*") {
		dirPattern := strings.TrimSuffix(pattern, "/*")
		return strings.HasPrefix(path, dirPattern+"/") || path == dirPattern
	}
	
	// Exact match
	return path == pattern
}

// copyFile copies a file from src to dst
func copyFile(src, dst string) error {
	// Create destination directory if it doesn't exist
	if err := os.MkdirAll(filepath.Dir(dst), 0755); err != nil {
		return err
	}

	// Read source file
	srcData, err := os.ReadFile(src)
	if err != nil {
		return err
	}

	// Write to destination
	return os.WriteFile(dst, srcData, 0644)
}
