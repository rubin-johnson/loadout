package main

import (
	"github.com/spf13/cobra"
)

var (
	target string
)

var rootCmd = &cobra.Command{
	Use:   "loadout",
	Short: "Loadout configuration management tool",
	Long:  "A tool for managing system configurations and dotfiles",
}

func init() {
	// Add persistent flag for target directory
	rootCmd.PersistentFlags().StringVar(&target, "target", "", "Target directory for operations")
	
	// Add all subcommands
	rootCmd.AddCommand(validateCmd)
	rootCmd.AddCommand(applyCmd)
	rootCmd.AddCommand(statusCmd)
	rootCmd.AddCommand(restoreCmd)
	rootCmd.AddCommand(captureCmd)
}
