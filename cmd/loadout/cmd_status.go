package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/rubin-johnson/loadout/internal/status"
	"github.com/rubin-johnson/loadout/internal/paths"
)

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show status of current configuration",
	Long:  "Show the status of the current configuration in the target directory",
	Args:  cobra.NoArgs,
	Run: func(cmd *cobra.Command, args []string) {
		targetDir, err := paths.GetTargetRoot(target)
		if err != nil {
			fmt.Fprintf(cmd.ErrOrStderr(), "error: %v\n", err)
			os.Exit(1)
		}
		if err := status.ShowStatus(targetDir, cmd.OutOrStdout()); err != nil {
			fmt.Fprintf(cmd.ErrOrStderr(), "Status check failed: %v\n", err)
			os.Exit(1)
		}
	},
}
