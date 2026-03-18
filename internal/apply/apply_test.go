package apply_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/cline/loadout/internal/apply"
	"github.com/cline/loadout/internal/manifest"
)

func TestResolveDest(t *testing.T) {
	cases := []struct{ in string; wantSuffix string; ok bool }{
		{"~/.claude/CLAUDE.md", "CLAUDE.md", true},
		{"~/dotfile", "dotfile", true},
		{"/absolute/path", "", false},
		{"relative/path", "relative/path", true},
	}
	for _, c := range cases {
		got, ok := apply.ResolveDest(c.in, "/target")
		if ok != c.ok {
			t.Errorf("resolveDest(%q) ok=%v want %v", c.in, ok, c.ok)
		}
		if ok && !strings.HasSuffix(got, c.wantSuffix) {
			t.Errorf("resolveDest(%q) = %q want suffix %q", c.in, got, c.wantSuffix)
		}
	}
}

func TestAtomicApplyLandsFiles(t *testing.T) {
	bundle, target := makeValidBundle(t), t.TempDir()
	m, _ := manifest.Load(bundle)
	if err := apply.AtomicApply(bundle, target, m); err != nil {
		t.Fatal(err)
	}
	// at least one target file should exist in target dir
	// Check that files were actually moved to target
	entries, err := os.ReadDir(target)
	if err != nil {
		t.Fatal(err)
	}
	if len(entries) == 0 {
		t.Error("no files found in target directory after AtomicApply")
	}
}

// makeValidBundle creates a temporary bundle directory with test files
func makeValidBundle(t *testing.T) string {
	bundleDir := t.TempDir()

	// Create a manifest file
	manifestContent := `entries:
  - source: test.txt
    destination: ~/test.txt
  - source: subdir/nested.txt
    destination: ~/.claude/nested.txt
`
	if err := os.WriteFile(filepath.Join(bundleDir, "manifest.yaml"), []byte(manifestContent), 0644); err != nil {
		t.Fatal(err)
	}

	// Create test files
	if err := os.WriteFile(filepath.Join(bundleDir, "test.txt"), []byte("test content"), 0644); err != nil {
		t.Fatal(err)
	}

	if err := os.MkdirAll(filepath.Join(bundleDir, "subdir"), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(bundleDir, "subdir", "nested.txt"), []byte("nested content"), 0644); err != nil {
		t.Fatal(err)
	}

	return bundleDir
}
