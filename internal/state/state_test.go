package state

import (
	"testing"
)

func TestReadNilWhenMissing(t *testing.T) {
	s, err := Read(t.TempDir())
	if err != nil || s != nil {
		t.Fatalf("want nil,nil got %v,%v", s, err)
	}
}

func TestWriteAndRead(t *testing.T) {
	dir := t.TempDir()
	if err := Write(dir, &State{Active: "my-bundle"}); err != nil {
		t.Fatal(err)
	}
	s, err := Read(dir)
	if err != nil {
		t.Fatal(err)
	}
	if s.Active != "my-bundle" {
		t.Errorf("got %q", s.Active)
	}
}

func TestClearThenReadNil(t *testing.T) {
	dir := t.TempDir()
	Write(dir, &State{Active: "x"})
	Clear(dir)
	s, _ := Read(dir)
	if s != nil {
		t.Error("state should be nil after clear")
	}
}
