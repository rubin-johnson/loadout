package integration_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"testing"
)

func repoRoot(t *testing.T) string {
	t.Helper()
	_, filename, _, _ := runtime.Caller(0)
	dir := filepath.Dir(filename)
	
	// Walk up until we find go.mod
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatal("could not find go.mod")
		}
		dir = parent
	}
}

func buildBinary(t *testing.T) string {
	t.Helper()
	bin := filepath.Join(t.TempDir(), "loadout")
	if runtime.GOOS == "windows" {
		bin += ".exe"
	}
	cmd := exec.Command("go", "build", "-o", bin, "./cmd/loadout")
	cmd.Dir = repoRoot(t)
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("build failed: %v\n%s", err, out)
	}
	return bin
}

func makeValidBundle(t *testing.T) string {
	t.Helper()
	tmpDir := t.TempDir()
	bundleDir := filepath.Join(tmpDir, "bundle")
	err := os.MkdirAll(bundleDir, 0755)
	if err != nil {
		t.Fatal(err)
	}
	
	// Create a simple manifest.yaml
	manifestContent := `name: smoke
version: 0.0.1
author: ci
description: smoke test
targets:
  - path: CLAUDE.md
    dest: CLAUDE.md
`
	err = os.WriteFile(filepath.Join(bundleDir, "manifest.yaml"), []byte(manifestContent), 0644)
	if err != nil {
		t.Fatal(err)
	}
	
	// Create the test file
	err = os.WriteFile(filepath.Join(bundleDir, "CLAUDE.md"), []byte("# smoke"), 0644)
	if err != nil {
		t.Fatal(err)
	}
	
	return bundleDir
}

func TestSmokeValidate(t *testing.T) {
	t.Skip("pending STORY-014")
}

func TestSmokeApply(t *testing.T) {
	t.Skip("pending STORY-014")
}

func TestSmokeStatusNoState(t *testing.T) {
	t.Skip("pending STORY-014")
}

func TestSmokeRestore(t *testing.T) {
	t.Skip("pending STORY-014")
}

func TestSmokeCapture(t *testing.T) {
	t.Skip("pending STORY-014")
}