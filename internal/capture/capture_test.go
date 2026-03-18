package capture

import (
	"os"
	"path/filepath"
	"testing"
)

func TestCaptureBundleCreatesManifest(t *testing.T) {
	src := t.TempDir()
	os.WriteFile(filepath.Join(src, "CLAUDE.md"), []byte("# test"), 0644)
	out := filepath.Join(t.TempDir(), "bundle")
	if err := CaptureBundle(src, out, false); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(out, "manifest.yaml")); err != nil {
		t.Error("manifest.yaml not created")
	}
}

func TestCaptureRejectsExistingWithoutOverwrite(t *testing.T) {
	err := CaptureBundle(t.TempDir(), t.TempDir(), false)
	if err == nil {
		t.Error("expected error for existing output dir")
	}
}

func TestCaptureSkipsDBFiles(t *testing.T) {
	src := t.TempDir()
	os.WriteFile(filepath.Join(src, "data.db"), []byte("binary"), 0644)
	out := filepath.Join(t.TempDir(), "bundle")
	CaptureBundle(src, out, false)
	if _, err := os.Stat(filepath.Join(out, "data.db")); err == nil {
		t.Error(".db file must not be captured")
	}
}

// Additional tests for comprehensive coverage
func TestIsDBFile(t *testing.T) {
	tests := []struct {
		name     string
		filename string
		want     bool
	}{
		{"database file", "data.db", true},
		{"uppercase db", "DATA.DB", true},
		{"mixed case", "Data.Db", true},
		{"not db file", "data.txt", false},
		{"db in middle", "data.db.txt", false},
		{"empty string", "", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := isDBFile(tt.filename); got != tt.want {
				t.Errorf("isDBFile(%q) = %v, want %v", tt.filename, got, tt.want)
			}
		})
	}
}

func TestCaptureWithOverwrite(t *testing.T) {
	src := t.TempDir()
	os.WriteFile(filepath.Join(src, "CLAUDE.md"), []byte("# test"), 0644)
	out := t.TempDir() // existing directory
	
	// Should succeed with overwrite=true
	if err := CaptureBundle(src, out, true); err != nil {
		t.Fatal(err)
	}
	
	// Check manifest was created
	if _, err := os.Stat(filepath.Join(out, "manifest.yaml")); err != nil {
		t.Error("manifest.yaml not created")
	}
}

func TestCaptureGeneratesStubWhenNoTargets(t *testing.T) {
	src := t.TempDir()
	// Create a file that won't match any patterns
	os.WriteFile(filepath.Join(src, "random.txt"), []byte("content"), 0644)
	out := filepath.Join(t.TempDir(), "bundle")
	
	if err := CaptureBundle(src, out, false); err != nil {
		t.Fatal(err)
	}
	
	// Should have created stub CLAUDE.md
	if _, err := os.Stat(filepath.Join(out, "CLAUDE.md")); err != nil {
		t.Error("stub CLAUDE.md not created when no targets found")
	}
	
	// Should not have copied the random file
	if _, err := os.Stat(filepath.Join(out, "random.txt")); err == nil {
		t.Error("non-matching file should not be captured")
	}
}
