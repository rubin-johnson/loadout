package apply

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/rubin-johnson/loadout/internal/backup"
	"github.com/rubin-johnson/loadout/internal/state"
)

// bundleManifest represents the manifest.json structure in a bundle
type bundleManifest struct {
	Name        string        `json:"name"`
	Version     string        `json:"version"`
	Description string        `json:"description"`
	Targets     []targetEntry `json:"targets"`
}

// targetEntry represents one file mapping in the manifest
type targetEntry struct {
	Source string `json:"source"`
	Dest   string `json:"dest"`
}

// destEntry pairs a targetEntry with its resolved destination path
type destEntry struct {
	entry targetEntry
	dst   string
}

// loadBundleManifest reads and parses manifest.json from bundleDir
func loadBundleManifest(bundleDir string) (*bundleManifest, error) {
	manifestPath := filepath.Join(bundleDir, "manifest.json")
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read manifest.json: %w", err)
	}
	var m bundleManifest
	if err := json.Unmarshal(data, &m); err != nil {
		return nil, fmt.Errorf("failed to parse manifest.json: %w", err)
	}
	if m.Name == "" {
		return nil, fmt.Errorf("manifest missing required field: name")
	}
	if m.Version == "" {
		return nil, fmt.Errorf("manifest missing required field: version")
	}
	return &m, nil
}

// resolveDest resolves a destination path relative to targetDir.
// Strips ~/.claude/ and ~/ prefixes; skips absolute paths.
func resolveDest(dest, targetDir string) (string, bool) {
	if dest == "" {
		return "", false
	}

	// Handle absolute paths - skip them
	if filepath.IsAbs(dest) {
		return "", false
	}

	// Strip ~/.claude/ prefix
	if strings.HasPrefix(dest, "~/.claude/") {
		suffix := strings.TrimPrefix(dest, "~/.claude/")
		return filepath.Join(targetDir, suffix), true
	}

	// Strip ~/ prefix
	if strings.HasPrefix(dest, "~/") {
		suffix := strings.TrimPrefix(dest, "~/")
		return filepath.Join(targetDir, suffix), true
	}

	// Relative path - join with target dir
	return filepath.Join(targetDir, dest), true
}

// ApplyBundle orchestrates validation, backup, atomic placement, and state writing.
// If dryRun is true, it prints planned copies to stdout and returns nil without
// touching the filesystem.
func ApplyBundle(bundleDir, targetDir string, dryRun bool) error {
	// Step 1: Validate — load and validate the manifest
	m, err := loadBundleManifest(bundleDir)
	if err != nil {
		return fmt.Errorf("invalid bundle: %w", err)
	}

	// Step 2: Resolve destinations once per entry
	var entries []destEntry
	for _, t := range m.Targets {
		dst, ok := resolveDest(t.Dest, targetDir)
		if ok {
			entries = append(entries, destEntry{t, dst})
		}
	}

	// Dry-run: print planned copies and return without touching the filesystem
	if dryRun {
		for _, e := range entries {
			fmt.Printf("copy %s -> %s\n", filepath.Join(bundleDir, e.entry.Source), e.dst)
		}
		return nil
	}

	// Step 3: Backup — always create a backup before applying
	backupTimestamp, err := backup.CreateBackup(targetDir)
	if err != nil {
		return fmt.Errorf("failed to create backup: %w", err)
	}

	// Step 4: Apply — atomically copy files to their destinations
	var placedPaths []string
	for _, e := range entries {
		src := filepath.Join(bundleDir, e.entry.Source)
		if err := os.MkdirAll(filepath.Dir(e.dst), 0755); err != nil {
			return fmt.Errorf("failed to create destination directory for %s: %w", e.dst, err)
		}
		if err := copyFile(src, e.dst); err != nil {
			return fmt.Errorf("failed to copy %s to %s: %w", e.entry.Source, e.dst, err)
		}
		placedPaths = append(placedPaths, e.dst)
	}

	// Step 5: Write state
	s := &state.State{
		Active:          m.Name,
		AppliedAt:       time.Now().Format(time.RFC3339),
		BundlePath:      bundleDir,
		ManifestVersion: m.Version,
		Backup:          backupTimestamp,
		PlacedPaths:     placedPaths,
	}
	if err := state.Write(targetDir, s); err != nil {
		return fmt.Errorf("failed to write state: %w", err)
	}

	return nil
}

// ResolveDest is the exported version of resolveDest for external use.
func ResolveDest(destStr, targetDir string) (string, bool) {
	return resolveDest(destStr, targetDir)
}

// AtomicApply stages all files to a sibling temp dir, then moves each to its final destination.
// This is kept for compatibility with the existing manifest.Manifest type.
func AtomicApply(bundleDir, targetDir string, entries []destEntry) error {
	// Create staging directory as sibling to target
	stagingDir, err := os.MkdirTemp(filepath.Dir(targetDir), "loadout-stage-*")
	if err != nil {
		return fmt.Errorf("failed to create staging dir: %w", err)
	}
	defer os.RemoveAll(stagingDir)

	// Build list of staged files before moving anything
	var staged []struct{ src, dst string }

	for _, e := range entries {
		// Source file in bundle
		src := filepath.Join(bundleDir, e.entry.Source)

		// Stage file to temp location
		stageFile := filepath.Join(stagingDir, e.entry.Source)
		if err := os.MkdirAll(filepath.Dir(stageFile), 0755); err != nil {
			return fmt.Errorf("failed to create staging dir for %s: %w", e.entry.Source, err)
		}

		// Copy to staging area
		if err := copyFile(src, stageFile); err != nil {
			return fmt.Errorf("failed to stage %s: %w", e.entry.Source, err)
		}

		staged = append(staged, struct{ src, dst string }{stageFile, e.dst})
	}

	// Now atomically move all staged files to their destinations
	for _, s := range staged {
		// Ensure destination directory exists
		if err := os.MkdirAll(filepath.Dir(s.dst), 0755); err != nil {
			return fmt.Errorf("failed to create dest dir for %s: %w", s.dst, err)
		}

		// Check if destination exists and is a directory
		if info, err := os.Stat(s.dst); err == nil && info.IsDir() {
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
