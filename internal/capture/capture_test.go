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
