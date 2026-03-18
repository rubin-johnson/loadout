package apply_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/rubin-johnson/loadout/internal/apply"
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
