package apply

import (
	"os"
	"path/filepath"
	"testing"

	"dotfiles-manager/internal/state"
)

func makeValidBundle(t *testing.T) string {
	bundleDir := t.TempDir()
	
	// Create manifest.json
	manifestContent := `{
	"name": "test-bundle",
	"version": "1.0.0",
	"description": "Test bundle",
	"targets": [
		{
			"source": "file1.txt",
			"dest": "file1.txt"
		}
	]
}`
	if err := os.WriteFile(filepath.Join(bundleDir, "manifest.json"), []byte(manifestContent), 0644); err != nil {
		t.Fatal(err)
	}
	
	// Create source file
	if err := os.WriteFile(filepath.Join(bundleDir, "file1.txt"), []byte("test content"), 0644); err != nil {
		t.Fatal(err)
	}
	
	return bundleDir
}

func TestApplyBundleWritesState(t *testing.T) {
	bundle, target := makeValidBundle(t), t.TempDir()
	if err := ApplyBundle(bundle, target, false); err != nil {
		t.Fatal(err)
	}
	s, _ := state.Read(target)
	if s == nil || s.Active == "" {
		t.Error("state not written")
	}
}

func TestApplyBundleCreatesBackup(t *testing.T) {
	bundle, target := makeValidBundle(t), t.TempDir()
	ApplyBundle(bundle, target, false)
	// Check if backup directory exists
	backupDir := filepath.Join(target, ".dotfiles", "backups")
	if _, err := os.Stat(backupDir); os.IsNotExist(err) {
		t.Error("backup not created")
	}
}

func TestApplyBundleDryRunNoChanges(t *testing.T) {
	bundle, target := makeValidBundle(t), t.TempDir()
	ApplyBundle(bundle, target, true)
	s, _ := state.Read(target)
	if s != nil {
		t.Error("dry-run must not write state")
	}
}

func TestApplyBundleInvalidBundleReturnsError(t *testing.T) {
	err := ApplyBundle(t.TempDir(), t.TempDir(), false)
	if err == nil {
		t.Error("expected error for invalid bundle")
	}
}

func TestApplyBundleWritesState(t *testing.T) {
	bundle, target := makeValidBundle(t), t.TempDir()
	if err := ApplyBundle(bundle, target, false); err != nil {
		t.Fatal(err)
	}
	s, _ := state.Read(target)
	if s == nil || s.Active == "" {
		t.Error("state not written")
	}
}

func TestApplyBundleCreatesBackup(t *testing.T) {
	bundle, target := makeValidBundle(t), t.TempDir()
	ApplyBundle(bundle, target, false)
	// Check if backup directory exists
	backupDir := filepath.Join(target, ".backups")
	if _, err := os.Stat(backupDir); os.IsNotExist(err) {
		t.Error("backup not created")
	}
}

func TestApplyBundleDryRunNoChanges(t *testing.T) {
	bundle, target := makeValidBundle(t), t.TempDir()
	ApplyBundle(bundle, target, true)
	s, _ := state.Read(target)
	if s != nil {
		t.Error("dry-run must not write state")
	}
}

func TestApplyBundleInvalidBundleReturnsError(t *testing.T) {
	err := ApplyBundle(t.TempDir(), t.TempDir(), false)
	if err == nil {
		t.Error("expected error for invalid bundle")
	}
}
