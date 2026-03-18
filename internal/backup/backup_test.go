package backup_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/rubin-johnson/loadout/internal/backup"
)

// makeValidBundle creates a temporary bundle directory for testing
func makeValidBundle(t *testing.T) string {
	t.Helper()
	tempDir := t.TempDir()
	bundleDir := filepath.Join(tempDir, "test-bundle")
	err := os.MkdirAll(bundleDir, 0755)
	if err != nil {
		t.Fatalf("Failed to create test bundle: %v", err)
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
