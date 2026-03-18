package backup_test

import (
	"os"
	"path/filepath"
	"testing"
	"github.com/rubin-johnson/loadout/internal/backup"
)

func makeValidBundle(t *testing.T) string {
	t.Helper()
	tmpDir := t.TempDir()
	bundleDir := filepath.Join(tmpDir, "bundle")
	err := os.MkdirAll(bundleDir, 0755)
	if err != nil {
		t.Fatal(err)
	}
	
	// Create a simple manifest.yaml
	manifestContent := `name: test
version: 0.1.0
author: test
description: test bundle
targets:
  - path: CLAUDE.md
    dest: CLAUDE.md
`
	err = os.WriteFile(filepath.Join(bundleDir, "manifest.yaml"), []byte(manifestContent), 0644)
	if err != nil {
		t.Fatal(err)
	}
	
	// Create the test file
	err = os.WriteFile(filepath.Join(bundleDir, "CLAUDE.md"), []byte("# test"), 0644)
	if err != nil {
		t.Fatal(err)
	}
	
	return bundleDir
}

func TestCreateBackupCopiesFiles(t *testing.T) {
	t.Skip("pending STORY-004")
}

func TestCreateBackupExcludesBackupDir(t *testing.T) {
	t.Skip("pending STORY-004")
}

func TestListBackupsSorted(t *testing.T) {
	t.Skip("pending STORY-004")
}

func TestGetLatestBackupNilWhenEmpty(t *testing.T) {
	t.Skip("pending STORY-004")
}

func TestGetLatestBackup(t *testing.T) {
	t.Skip("pending STORY-004")
}

func TestBackupEmptyTarget(t *testing.T) {
	t.Skip("pending STORY-004")
}
