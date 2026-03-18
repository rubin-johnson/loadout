package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/rubin-johnson/loadout/internal/apply"
	"github.com/rubin-johnson/loadout/internal/paths"
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
		
		targetDir, err := paths.GetTargetRoot(target)
		if err != nil {
			fmt.Fprintf(cmd.ErrOrStderr(), "error: %v\n", err)
			os.Exit(1)
		}
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
