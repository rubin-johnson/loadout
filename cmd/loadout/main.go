package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "loadout",
	Short: "Loadout CLI tool",
	Long:  "A CLI tool for managing loadouts",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Loadout CLI v1.0.0")
	},
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
