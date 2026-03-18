package apply_test

import (
	"os"
	"path/filepath"
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
	manifestContent := `name: test
version: 0.1.0
author: test
description: test bundle
targets:
  - path: CLAUDE.md
    dest: CLAUDE.md
`
	err = os.WriteFile(filepath.Join(bundleDir, "manifest.yaml"), []byte(manifestContent), 0644)
	if err != nil {
		t.Fatal(err)
	}
	
	// Create the test file
	err = os.WriteFile(filepath.Join(bundleDir, "CLAUDE.md"), []byte("# test"), 0644)
	if err != nil {
		t.Fatal(err)
	}
	
	return bundleDir
}

func TestFilesLandAtCorrectPaths(t *testing.T) {
	t.Skip("pending STORY-009")
}

func TestUnrelatedFilesUntouched(t *testing.T) {
	t.Skip("pending STORY-009")
}

func TestTildeDestResolvesToTarget(t *testing.T) {
	t.Skip("pending STORY-009")
}

func TestAtomicOnMoveFailure(t *testing.T) {
	t.Skip("pending STORY-009")
}

func TestApplyWritesState(t *testing.T) {
	t.Skip("pending STORY-010")
}

func TestApplyCreatesBackup(t *testing.T) {
	t.Skip("pending STORY-010")
}

func TestApplyDryRunNoChanges(t *testing.T) {
	t.Skip("pending STORY-010")
}

func TestInvalidBundleAborts(t *testing.T) {
	t.Skip("pending STORY-010")
}
