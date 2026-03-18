package validate

import (
	"os"
	"path/filepath"
	"testing"
)

func TestValidateNilPath(t *testing.T) {
	errs := ValidateBundle("")
	if len(errs) == 0 {
		t.Error("expected error for empty path")
	}
}

func TestValidateMissingTargetFile(t *testing.T) {
	dir := t.TempDir()
	data := "name: x\nversion: 0.0.1\nauthor: a\ndescription: d\ntargets:\n  - path: missing.txt\n    dest: missing.txt\n"
	os.WriteFile(filepath.Join(dir, "manifest.yaml"), []byte(data), 0644)
	errs := ValidateBundle(dir)
	if len(errs) == 0 {
		t.Error("expected error for missing target file")
	}
}

func TestValidateValid(t *testing.T) {
	errs := ValidateBundle(makeValidBundle(t))
	if len(errs) != 0 {
		t.Errorf("unexpected errors: %v", errs)
	}
}

// Helper function to create a valid bundle for testing
func makeValidBundle(t *testing.T) string {
	dir := t.TempDir()
	data := "name: testapp\nversion: 1.0.0\nauthor: testauthor\ndescription: test description\ntargets:\n  - path: test.txt\n    dest: test.txt\n"
	err := os.WriteFile(filepath.Join(dir, "manifest.yaml"), []byte(data), 0644)
	if err != nil {
		t.Fatal(err)
	}
	// Create the target file
	err = os.WriteFile(filepath.Join(dir, "test.txt"), []byte("test content"), 0644)
	if err != nil {
		t.Fatal(err)
	}
	return dir
}
