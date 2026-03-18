package paths

import (
	"os"
	"path/filepath"
)

// GetTargetRoot resolves the target directory based on CLI flag, env var, or default.
// Priority: cliTarget > LOADOUT_TARGET_ROOT env var > $HOME/.claude
func GetTargetRoot(cliTarget string) (string, error) {
	// 1. CLI target takes precedence
	if cliTarget != "" {
		return cliTarget, nil
	}

	// 2. Check environment variable
	if envTarget := os.Getenv("LOADOUT_TARGET_ROOT"); envTarget != "" {
		return envTarget, nil
	}

	// 3. Default to $HOME/.claude
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}

	return filepath.Join(home, ".claude"), nil
}
