package integration_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"testing"
)

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

func buildBinary(t *testing.T) string {
	t.Helper()
	tmpDir := t.TempDir()
	binaryPath := filepath.Join(tmpDir, "loadout")
	if runtime.GOOS == "windows" {
		binaryPath += ".exe"
	}
	
	cmd := exec.Command("go", "build", "-o", binaryPath, "./cmd/loadout")
	err := cmd.Run()
	if err != nil {
		t.Fatalf("Failed to build binary: %v", err)
	}
	
	return binaryPath
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
