package secrets

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestScanDetectsAPIKey(t *testing.T) {
	f := filepath.Join(t.TempDir(), "cfg.txt")
	os.WriteFile(f, []byte("api_key = \"supersecrettoken12345678\"\n"), 0644)
	warns, err := ScanForSecrets(f)
	if err != nil {
		t.Fatal(err)
	}
	if len(warns) == 0 {
		t.Error("expected at least one warning")
	}
	if !strings.Contains(warns[0], "Line 1") {
		t.Errorf("missing line number: %q", warns[0])
	}
}

func TestScanCleanFile(t *testing.T) {
	f := filepath.Join(t.TempDir(), "clean.txt")
	os.WriteFile(f, []byte("# just a comment\nfoo = bar\n"), 0644)
	warns, err := ScanForSecrets(f)
	if err != nil || len(warns) != 0 {
		t.Errorf("unexpected: %v %v", warns, err)
	}
}
