package status

import (
	"fmt"
	"io"

	"github.com/rubin-johnson/loadout/internal/state"
)

// ShowStatus prints the active loadout summary to the provided writer.
// If no loadout is applied, it prints "No loadout applied" message.
func ShowStatus(targetDir string, w io.Writer) error {
	// Try to read the state from the target directory
	currentState, err := state.Read(targetDir)
	if err != nil || currentState == nil {
		// No state file or error reading it - no loadout applied
		fmt.Fprintf(w, "No loadout applied\n")
		return nil
	}

	// Print the loadout information
	fmt.Fprintf(w, "Active loadout: %s\n", currentState.Active)
	fmt.Fprintf(w, "Version: %s\n", currentState.ManifestVersion)
	if currentState.AppliedAt != "" {
		fmt.Fprintf(w, "Applied at: %s\n", currentState.AppliedAt)
	}
	if currentState.BundlePath != "" {
		fmt.Fprintf(w, "Bundle path: %s\n", currentState.BundlePath)
	}
	if currentState.Backup != "" {
		fmt.Fprintf(w, "Backup name: %s\n", currentState.Backup)
	}

	return nil
}
