package apply

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/cline/loadout/internal/manifest"
)

// ResolveDest strips ~/.claude/ and ~/ prefixes; returns "", false for absolute paths
func ResolveDest(destStr, targetDir string) (string, bool) {
	// Handle absolute paths - skip them
	if filepath.IsAbs(destStr) {
		return "", false
	}

	// Strip ~/.claude/ prefix
	if strings.HasPrefix(destStr, "~/.claude/") {
		suffix := strings.TrimPrefix(destStr, "~/.claude/")
		return filepath.Join(targetDir, suffix), true
	}

	// Strip ~/ prefix
	if strings.HasPrefix(destStr, "~/") {
		suffix := strings.TrimPrefix(destStr, "~/")
		return filepath.Join(targetDir, suffix), true
	}

	// Relative path - join with target dir
	return filepath.Join(targetDir, destStr), true
}

// AtomicApply stages all files to a sibling temp dir, then moves each to its final destination
func AtomicApply(bundleDir, targetDir string, m *manifest.Manifest) error {
	// Create staging directory as sibling to target
	stagingDir, err := os.MkdirTemp(filepath.Dir(targetDir), "loadout-stage-*")
	if err != nil {
		return fmt.Errorf("failed to create staging dir: %w", err)
	}
	defer os.RemoveAll(stagingDir)

	// Build list of staged files before moving anything
	var staged []struct{ src, dst string }

	for _, entry := range m.Entries {
		// Resolve destination
		dest, ok := ResolveDest(entry.Destination, targetDir)
		if !ok {
			// Skip absolute paths (not an error)
			continue
		}

		// Source file in bundle
		src := filepath.Join(bundleDir, entry.Source)

		// Stage file to temp location
		stageFile := filepath.Join(stagingDir, entry.Source)
		if err := os.MkdirAll(filepath.Dir(stageFile), 0755); err != nil {
			return fmt.Errorf("failed to create staging dir for %s: %w", entry.Source, err)
		}

		// Copy to staging area
		if err := copyFile(src, stageFile); err != nil {
			return fmt.Errorf("failed to stage %s: %w", entry.Source, err)
		}

		staged = append(staged, struct{ src, dst string }{stageFile, dest})
	}

	// Now atomically move all staged files to their destinations
	for _, s := range staged {
		// Ensure destination directory exists
		if err := os.MkdirAll(filepath.Dir(s.dst), 0755); err != nil {
			return fmt.Errorf("failed to create dest dir for %s: %w", s.dst, err)
		}

		// Check if destination exists and is a directory
		if info, err := os.Stat(s.dst); err == nil && info.IsDir() {
			// Directory destination: RemoveAll then Rename
			if err := os.RemoveAll(s.dst); err != nil {
				return fmt.Errorf("failed to remove existing dir %s: %w", s.dst, err)
			}
		}

		// Atomic move (rename)
		if err := os.Rename(s.src, s.dst); err != nil {
			return fmt.Errorf("failed to move %s to %s: %w", s.src, s.dst, err)
		}
	}

	return nil
}

// copyFile copies a file from src to dst
func copyFile(src, dst string) error {
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