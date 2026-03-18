package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/rubin-johnson/loadout/internal/restore"
	"github.com/rubin-johnson/loadout/internal/paths"
)

var (
	backupName string
)

var restoreCmd = &cobra.Command{
	Use:   "restore",
	Short: "Restore from a backup",
	Long:  "Restore configuration from a backup to the target directory",
	Args:  cobra.NoArgs,
	Run: func(cmd *cobra.Command, args []string) {
		targetDir, err := paths.GetTargetRoot(target)
		if err != nil {
			fmt.Fprintf(cmd.ErrOrStderr(), "error: %v\n", err)
			os.Exit(1)
		}
		if err := restore.RestoreBundle(targetDir, backupName); err != nil {
			fmt.Fprintf(cmd.ErrOrStderr(), "Restore failed: %v\n", err)
			os.Exit(1)
		}
		
		fmt.Fprintf(cmd.OutOrStdout(), "Restore completed successfully\n")
	},
}

func init() {
	restoreCmd.Flags().StringVar(&backupName, "backup", "", "Name of the backup to restore")
}
