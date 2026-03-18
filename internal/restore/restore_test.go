package restore

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/wesen/loadout/internal/backup"
	"github.com/wesen/loadout/internal/state"
)

func TestRestoreUsesPlacedPaths(t *testing.T) {
	target := t.TempDir()
	os.WriteFile(filepath.Join(target, "placed.txt"), []byte("x"), 0644)
	os.WriteFile(filepath.Join(target, "unrelated.txt"), []byte("y"), 0644)
	bkpName, _ := backup.Create(target)
	state.Write(target, &state.State{
		Backup:      bkpName,
		PlacedPaths: []string{filepath.Join(target, "placed.txt")},
	})
	RestoreBundle(target, "")
	if _, err := os.Stat(filepath.Join(target, "unrelated.txt")); err != nil {
		t.Error("unrelated file should survive restore")
	}
}

func TestRestoreNoBackupsError(t *testing.T) {
	err := RestoreBundle(t.TempDir(), "")
	if err == nil {
		t.Error("expected error when no backups exist")
	}
}

func TestRestoreClearsState(t *testing.T) {
	target := t.TempDir()
	bkpName, _ := backup.Create(target)
	state.Write(target, &state.State{Backup: bkpName})
	RestoreBundle(target, "")
	s, _ := state.Read(target)
	if s != nil {
		t.Error("state should be cleared after restore")
	}
}
