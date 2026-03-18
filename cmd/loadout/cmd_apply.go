package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/loadout/internal/apply"
	"github.com/loadout/internal/paths"
)

var (
	dryRun bool
)

var applyCmd = &cobra.Command{
	Use:   "apply <bundle>",
	Short: "Apply a bundle configuration",
	Long:  "Apply a bundle configuration to the target directory",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		bundlePath := args[0]
		
		targetDir := paths.GetTargetRoot(target)
		if err := apply.ApplyBundle(bundlePath, targetDir, dryRun); err != nil {
			fmt.Fprintf(cmd.ErrOrStderr(), "Apply failed: %v\n", err)
			os.Exit(1)
		}
		
		if dryRun {
			fmt.Fprintf(cmd.OutOrStdout(), "Dry run completed successfully\n")
		} else {
			fmt.Fprintf(cmd.OutOrStdout(), "Bundle applied successfully\n")
		}
	},
}

func init() {
	applyCmd.Flags().BoolVar(&dryRun, "dry-run", false, "Show what would be done without making changes")
}
