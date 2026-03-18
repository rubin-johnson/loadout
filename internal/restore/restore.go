package restore

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/rubin-johnson/loadout/internal/backup"
	"github.com/rubin-johnson/loadout/internal/state"
)

// RestoreBundle removes placed files and restores a backup
// Resolves backup via: explicit arg → state.Backup → filesystem scan
func RestoreBundle(targetDir, backupName string) error {
	// Read current state
	currentState, err := state.Read(targetDir)
	if err != nil {
		// State read error is not fatal, we can still try to restore
		currentState = nil
	}

	// Resolve backup name
	resolvedBackupName := backupName
	if resolvedBackupName == "" && currentState != nil {
		resolvedBackupName = currentState.Backup
	}

	// If still no backup name, scan filesystem for available backups
	if resolvedBackupName == "" {
		backupDir := filepath.Join(targetDir, backup.BackupDir)
		entries, err := os.ReadDir(backupDir)
		if err != nil || len(entries) == 0 {
			return fmt.Errorf("no backups exist and no backup name provided")
		}
		// Use the first available backup
		for _, entry := range entries {
			if entry.IsDir() {
				resolvedBackupName = entry.Name()
				break
			}
		}
		if resolvedBackupName == "" {
			return fmt.Errorf("no backups exist and no backup name provided")
		}
	}

	// Remove placed files
	if currentState != nil && len(currentState.PlacedPaths) > 0 {
		// Remove only placed paths
		for _, placedPath := range currentState.PlacedPaths {
			if err := os.RemoveAll(placedPath); err != nil {
				// Continue removing other files even if one fails
				continue
			}
		}
	} else {
		// Fallback: clear all except backup directory
		entries, err := os.ReadDir(targetDir)
		if err != nil {
			return fmt.Errorf("failed to read target directory: %w", err)
		}
		for _, entry := range entries {
			// Skip backup directory
			if entry.Name() == backup.BackupDir {
				continue
			}
			path := filepath.Join(targetDir, entry.Name())
			if err := os.RemoveAll(path); err != nil {
				// Continue removing other files even if one fails
				continue
			}
		}
	}

	// Restore from backup
	backupPath := filepath.Join(targetDir, backup.BackupDir, resolvedBackupName)
	if _, err := os.Stat(backupPath); os.IsNotExist(err) {
		return fmt.Errorf("backup %s does not exist", resolvedBackupName)
	}

	// Copy files from backup to target
	err = filepath.Walk(backupPath, func(srcPath string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Calculate relative path from backup root
		relPath, err := filepath.Rel(backupPath, srcPath)
		if err != nil {
			return err
		}

		// Skip the backup root itself
		if relPath == "." {
			return nil
		}

		destPath := filepath.Join(targetDir, relPath)

		if info.IsDir() {
			return os.MkdirAll(destPath, info.Mode())
		}

		// Copy file
		srcFile, err := os.Open(srcPath)
		if err != nil {
			return err
		}
		defer srcFile.Close()

		// Ensure destination directory exists
		if err := os.MkdirAll(filepath.Dir(destPath), 0755); err != nil {
			return err
		}

		destFile, err := os.Create(destPath)
		if err != nil {
			return err
		}
		defer destFile.Close()

		// Copy content
		_, err = destFile.ReadFrom(srcFile)
		if err != nil {
			return err
		}

		// Set file mode
		return os.Chmod(destPath, info.Mode())
	})

	if err != nil {
		return fmt.Errorf("failed to restore backup: %w", err)
	}

	// Clear state after successful restore
	if err := state.Clear(targetDir); err != nil {
		// State clear failure is not fatal for restore operation
		// but we should still report it
		return fmt.Errorf("restore completed but failed to clear state: %w", err)
	}

	return nil
}
