package backup

import (
	"os"
	"path/filepath"
	"testing"
)

func TestCreateBackupCopiesFiles(t *testing.T) {
	dir := t.TempDir()
	os.WriteFile(filepath.Join(dir, "cfg.txt"), []byte("data"), 0644)
	ts, err := CreateBackup(dir)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(dir, BackupDir, ts, "cfg.txt")); err != nil {
		t.Error("backed-up file missing")
	}
}

func TestCreateBackupExcludesBackupDir(t *testing.T) {
	dir := t.TempDir()
	os.MkdirAll(filepath.Join(dir, BackupDir, "old"), 0755)
	ts, _ := CreateBackup(dir)
	entries, _ := os.ReadDir(filepath.Join(dir, BackupDir, ts))
	for _, e := range entries {
		if e.Name() == BackupDir {
			t.Error("backup dir must not be nested")
		}
	}
}

func TestGetLatestBackupNilWhenEmpty(t *testing.T) {
	ts, err := GetLatestBackup(t.TempDir())
	if err != nil || ts != "" {
		t.Errorf("expected empty, got %q %v", ts, err)
	}
}
