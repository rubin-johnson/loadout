package status

import (
	"bytes"
	"strings"
	"testing"

	"github.com/ryanwclark1/project-loadout/internal/state"
)

func TestShowStatusNoState(t *testing.T) {
	var buf bytes.Buffer
	if err := ShowStatus(t.TempDir(), &buf); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(buf.String(), "No loadout") {
		t.Errorf("unexpected output: %q", buf.String())
	}
}

func TestShowStatusWithState(t *testing.T) {
	dir := t.TempDir()
	state.Write(dir, &state.State{Active: "my-bundle", ManifestVersion: "1.2.3"})
	var buf bytes.Buffer
	ShowStatus(dir, &buf)
	out := buf.String()
	if !strings.Contains(out, "my-bundle") || !strings.Contains(out, "1.2.3") {
		t.Errorf("missing fields in output: %q", out)
	}
}
