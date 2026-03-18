package state

import (
	"encoding/json"
	"os"
	"path/filepath"
)

// State represents the loadout application state
type State struct {
	Active          string   `json:"active"`
	AppliedAt       string   `json:"applied_at"`
	BundlePath      string   `json:"bundle_path"`
	ManifestVersion string   `json:"manifest_version"`
	Backup          string   `json:"backup"`
	PlacedPaths     []string `json:"placed_paths"`
}

const stateFileName = ".loadout-state.json"

// Read loads state from the target directory.
// Returns nil, nil when state file is absent.
func Read(targetDir string) (*State, error) {
	statePath := filepath.Join(targetDir, stateFileName)
	
	data, err := os.ReadFile(statePath)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	
	var state State
	if err := json.Unmarshal(data, &state); err != nil {
		return nil, err
	}
	
	return &state, nil
}

// Write serializes state to .loadout-state.json in the target directory.
func Write(targetDir string, s *State) error {
	statePath := filepath.Join(targetDir, stateFileName)
	
	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	
	return os.WriteFile(statePath, data, 0644)
}

// Clear removes the state file from the target directory.
// No error if the file is already absent.
func Clear(targetDir string) error {
	statePath := filepath.Join(targetDir, stateFileName)
	
	err := os.Remove(statePath)
	if os.IsNotExist(err) {
		return nil
	}
	return err
}
