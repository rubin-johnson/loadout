package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/loadout/internal/capture"
)

var (
	yes bool
)

var captureCmd = &cobra.Command{
	Use:   "capture <source> <output>",
	Short: "Capture configuration from source",
	Long:  "Capture configuration from a source directory and save as a bundle",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		sourcePath := args[0]
		outputPath := args[1]
		
		if err := capture.CaptureBundle(sourcePath, outputPath, yes); err != nil {
			fmt.Fprintf(cmd.ErrOrStderr(), "Capture failed: %v\n", err)
			os.Exit(1)
		}
		
		fmt.Fprintf(cmd.OutOrStdout(), "Capture completed successfully\n")
	},
}

func init() {
	captureCmd.Flags().BoolVar(&yes, "yes", false, "Automatically confirm all prompts")
}
