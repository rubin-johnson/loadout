package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/loadout/internal/validate"
)

var validateCmd = &cobra.Command{
	Use:   "validate <bundle>",
	Short: "Validate a bundle configuration",
	Long:  "Validate that a bundle configuration is correct and can be applied",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		bundlePath := args[0]
		
		if err := validate.ValidateBundle(bundlePath); err != nil {
			fmt.Fprintf(cmd.ErrOrStderr(), "Validation failed: %v\n", err)
			os.Exit(1)
		}
		
		fmt.Fprintf(cmd.OutOrStdout(), "Bundle validation successful\n")
	},
}
