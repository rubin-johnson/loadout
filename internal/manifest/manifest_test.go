package manifest

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadMissingFields(t *testing.T) {
	dir := t.TempDir()
	os.WriteFile(filepath.Join(dir, "manifest.yaml"), []byte("name: foo\n"), 0644)
	_, err := Load(dir)
	if err == nil {
		t.Fatal("expected error for missing fields")
	}
}

func TestLoadInvalidSemver(t *testing.T) {
	dir := t.TempDir()
	data := "name: x\nversion: notver\nauthor: a\ndescription: d\ntargets: []\n"
	os.WriteFile(filepath.Join(dir, "manifest.yaml"), []byte(data), 0644)
	_, err := Load(dir)
	if err == nil {
		t.Fatal("expected semver error")
	}
}

func TestLoadValid(t *testing.T) {
	dir := makeValidBundle(t)
	m, err := Load(dir)
	if err != nil {
		t.Fatal(err)
	}
	if m.Name == "" {
		t.Error("name empty")
	}
}

func TestToMap(t *testing.T) {
	m := &Manifest{Name: "x", Version: "1.0.0", Author: "a", Description: "d"}
	got := m.ToMap()
	if got["name"] != "x" {
		t.Errorf("got %v", got)
	}
}

// Helper function to create a valid bundle for testing
func makeValidBundle(t *testing.T) string {
	dir := t.TempDir()
	data := "name: testapp\nversion: 1.0.0\nauthor: testauthor\ndescription: test description\ntargets: []\n"
	err := os.WriteFile(filepath.Join(dir, "manifest.yaml"), []byte(data), 0644)
	if err != nil {
		t.Fatal(err)
	}
	return dir
}
