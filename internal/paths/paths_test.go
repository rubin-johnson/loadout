package paths

import (
	"os"
	"path/filepath"
	"testing"
)

func TestGetTargetRootCLIFlag(t *testing.T) {
	got, err := GetTargetRoot("/tmp/mydir")
	if err != nil || got != "/tmp/mydir" {
		t.Errorf("got %q %v", got, err)
	}
}

func TestGetTargetRootEnvVar(t *testing.T) {
	t.Setenv("LOADOUT_TARGET_ROOT", "/tmp/env-target")
	got, _ := GetTargetRoot("")
	if got != "/tmp/env-target" {
		t.Errorf("got %q", got)
	}
}

func TestGetTargetRootDefault(t *testing.T) {
	t.Setenv("LOADOUT_TARGET_ROOT", "")
	got, err := GetTargetRoot("")
	if err != nil {
		t.Fatal(err)
	}
	home, _ := os.UserHomeDir()
	if got != filepath.Join(home, ".claude") {
		t.Errorf("got %q", got)
	}
}
