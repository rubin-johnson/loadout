package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/loadout/internal/status"
	"github.com/loadout/internal/paths"
)

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show status of current configuration",
	Long:  "Show the status of the current configuration in the target directory",
	Args:  cobra.NoArgs,
	Run: func(cmd *cobra.Command, args []string) {
		targetDir := paths.GetTargetRoot(target)
		if err := status.ShowStatus(targetDir); err != nil {
			fmt.Fprintf(cmd.ErrOrStderr(), "Status check failed: %v\n", err)
			os.Exit(1)
		}
	},
}
