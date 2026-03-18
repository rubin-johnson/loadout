package backup

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"time"
)

// BackupDir is the directory name where backups are stored
const BackupDir = ".loadout-backups"

// CreateBackup copies all non-backup items to a timestamped subdir
// Returns the timestamp string
func CreateBackup(targetDir string) (string, error) {
	timestamp := time.Now().Format("2006-01-02-150405")
	backupPath := filepath.Join(targetDir, BackupDir, timestamp)
	
	if err := os.MkdirAll(backupPath, 0755); err != nil {
		return "", fmt.Errorf("failed to create backup directory: %w", err)
	}
	
	entries, err := os.ReadDir(targetDir)
	if err != nil {
		return "", fmt.Errorf("failed to read target directory: %w", err)
	}
	
	for _, entry := range entries {
		// Skip the backup directory itself
		if entry.Name() == BackupDir {
			continue
		}
		
		srcPath := filepath.Join(targetDir, entry.Name())
		dstPath := filepath.Join(backupPath, entry.Name())
		
		if entry.IsDir() {
			if err := copyDir(srcPath, dstPath); err != nil {
				return "", fmt.Errorf("failed to copy directory %s: %w", entry.Name(), err)
			}
		} else {
			if err := copyFile(srcPath, dstPath); err != nil {
				return "", fmt.Errorf("failed to copy file %s: %w", entry.Name(), err)
			}
		}
	}
	
	return timestamp, nil
}

// ListBackups returns sorted names matching timestamp pattern
func ListBackups(targetDir string) ([]string, error) {
	backupDirPath := filepath.Join(targetDir, BackupDir)
	
	// Check if backup directory exists
	if _, err := os.Stat(backupDirPath); os.IsNotExist(err) {
		return []string{}, nil
	}
	
	entries, err := os.ReadDir(backupDirPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read backup directory: %w", err)
	}
	
	// Pattern for timestamp format: YYYY-MM-DD-HHMMSS
	timestampPattern := regexp.MustCompile(`^\d{4}-\d{2}-\d{2}-\d{6}$`)
	
	var backups []string
	for _, entry := range entries {
		if entry.IsDir() && timestampPattern.MatchString(entry.Name()) {
			backups = append(backups, entry.Name())
		}
	}
	
	sort.Strings(backups)
	return backups, nil
}

// GetLatestBackup returns the most recent backup timestamp, or empty string if none exist
func GetLatestBackup(targetDir string) (string, error) {
	backups, err := ListBackups(targetDir)
	if err != nil {
		return "", err
	}
	
	if len(backups) == 0 {
		return "", nil
	}
	
	return backups[len(backups)-1], nil
}

// copyDir recursively copies a directory
func copyDir(src, dst string) error {
	return filepath.WalkDir(src, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		
		// Calculate relative path from src
		relPath, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}
		
		dstPath := filepath.Join(dst, relPath)
		
		if d.IsDir() {
			return os.MkdirAll(dstPath, d.Type().Perm())
		}
		
		return copyFile(path, dstPath)
	})
}

// copyFile copies a single file
func copyFile(src, dst string) error {
	srcFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer srcFile.Close()
	
	// Get source file info for permissions
	srcInfo, err := srcFile.Stat()
	if err != nil {
		return err
	}
	
	dstFile, err := os.OpenFile(dst, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, srcInfo.Mode())
	if err != nil {
		return err
	}
	defer dstFile.Close()
	
	_, err = io.Copy(dstFile, srcFile)
	return err
}
