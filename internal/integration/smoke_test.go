package integration

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
	cmd := exec.Command("go", "build", "-o", bin, "./cmd/loadout")
	cmd.Dir = repoRoot(t)
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("build failed: %v\n%s", err, out)
	}
	return bin
}

func makeValidBundle(t *testing.T) string {
	t.Helper()
	bundleDir := t.TempDir()
	bundlePath := filepath.Join(bundleDir, "bundle.yaml")
	
	// Create a minimal valid bundle
	content := `name: test-bundle
version: 1.0.0
files: []
configs: []
`
	if err := os.WriteFile(bundlePath, []byte(content), 0644); err != nil {
		t.Fatalf("failed to create bundle: %v", err)
	}
	
	return bundleDir
}

func TestSmokeValidate(t *testing.T) {
	bin, bundle := buildBinary(t), makeValidBundle(t)
	out, err := exec.Command(bin, "validate", bundle).CombinedOutput()
	if err != nil {
		t.Fatalf("validate failed: %v\n%s", err, out)
	}
}

func TestSmokeApply(t *testing.T) {
	bin, bundle, target := buildBinary(t), makeValidBundle(t), t.TempDir()
	out, err := exec.Command(bin, "apply", bundle, "--target", target).CombinedOutput()
	if err != nil {
		t.Fatalf("apply failed: %v\n%s", err, out)
	}
}
