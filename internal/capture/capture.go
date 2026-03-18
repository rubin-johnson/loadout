package capture

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"

	"loadout-manager/internal/secrets"
)

// DEFAULT_CAPTURES defines the files and directories to capture
var DEFAULT_CAPTURES = []string{
	"CLAUDE.md",
	".cursor/rules",
	".vscode/settings.json",
	"pyproject.toml",
	"requirements.txt",
	"package.json",
	"go.mod",
	"Dockerfile",
	"docker-compose.yml",
	"README.md",
	".env.example",
	"config",
	"scripts",
}

// SCAN_DIRS defines directories to scan for secrets
var SCAN_DIRS = []string{
	"config",
	"scripts",
	".cursor/rules",
}

// Manifest represents the structure of manifest.yaml
type Manifest struct {
	Version   string            `yaml:"version"`
	Captured  []string          `yaml:"captured"`
	Metadata  map[string]string `yaml:"metadata"`
	Generated []string          `yaml:"generated,omitempty"`
}

// isDBFile checks if a file is a database file that should be skipped
func isDBFile(name string) bool {
	return strings.HasSuffix(strings.ToLower(name), ".db")
}

// CaptureBundle copies DEFAULT_CAPTURES entries from sourceDir to outputDir and writes manifest.yaml
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
	var generated []string

	// Copy DEFAULT_CAPTURES entries
	for _, item := range DEFAULT_CAPTURES {
		srcPath := filepath.Join(sourceDir, item)
		dstPath := filepath.Join(outputDir, item)

		if info, err := os.Stat(srcPath); err == nil {
			if info.IsDir() {
				if err := copyDir(srcPath, dstPath); err != nil {
					return fmt.Errorf("failed to copy directory %s: %w", item, err)
				}
			} else {
				if err := copyFile(srcPath, dstPath); err != nil {
					return fmt.Errorf("failed to copy file %s: %w", item, err)
				}
			}
			captured = append(captured, item)
		}
	}

	// Scan for secrets in SCAN_DIRS
	for _, dir := range SCAN_DIRS {
		scanPath := filepath.Join(sourceDir, dir)
		if _, err := os.Stat(scanPath); err == nil {
			warnings := secrets.ScanForSecrets(scanPath)
			for _, warning := range warnings {
				fmt.Fprintf(os.Stderr, "WARNING: %s\n", warning)
			}
		}
	}

	// Generate stub CLAUDE.md if no targets were captured
	claudeFound := false
	for _, item := range captured {
		if item == "CLAUDE.md" {
			claudeFound = true
			break
		}
	}

	if !claudeFound {
		stubPath := filepath.Join(outputDir, "CLAUDE.md")
		stubContent := "# Project Configuration\n\nThis bundle was generated automatically.\n"
		if err := os.WriteFile(stubPath, []byte(stubContent), 0644); err != nil {
			return fmt.Errorf("failed to create stub CLAUDE.md: %w", err)
		}
		generated = append(generated, "CLAUDE.md")
	}

	// Create manifest
	manifest := Manifest{
		Version:  "1.0",
		Captured: captured,
		Metadata: map[string]string{
			"source": sourceDir,
			"type":   "capture",
		},
		Generated: generated,
	}

	// Write manifest.yaml
	manifestPath := filepath.Join(outputDir, "manifest.yaml")
	manifestData, err := yaml.Marshal(&manifest)
	if err != nil {
		return fmt.Errorf("failed to marshal manifest: %w", err)
	}

	if err := os.WriteFile(manifestPath, manifestData, 0644); err != nil {
		return fmt.Errorf("failed to write manifest: %w", err)
	}

	return nil
}

// copyFile copies a single file from src to dst
func copyFile(src, dst string) error {
	// Create destination directory if needed
	if err := os.MkdirAll(filepath.Dir(dst), 0755); err != nil {
		return err
	}

	srcFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer srcFile.Close()

	dstFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer dstFile.Close()

	_, err = io.Copy(dstFile, srcFile)
	return err
}

// copyDir recursively copies a directory from src to dst, skipping .db files
func copyDir(src, dst string) error {
	return filepath.WalkDir(src, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}

		// Skip .db files
		if !d.IsDir() && isDBFile(d.Name()) {
			return nil
		}

		// Calculate relative path and destination
		relPath, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}
		dstPath := filepath.Join(dst, relPath)

		if d.IsDir() {
			return os.MkdirAll(dstPath, 0755)
		} else {
			return copyFile(path, dstPath)
		}
	})
}
