package secrets

import (
	"os"
	"regexp"
	"strings"
	"fmt"
)

type secretPattern struct {
	label string
	re    *regexp.Regexp
}

// patterns contains regex patterns for detecting common secrets
var patterns = []secretPattern{
	{"AWS Secret Key", regexp.MustCompile(`AKIA[0-9A-Z]{16}`)},
	{"AWS Secret Key", regexp.MustCompile(`aws_secret_access_key\s*=\s*["']?[A-Za-z0-9/+=]{40}["']?`)},
	{"Generic API Key", regexp.MustCompile(`(?i)api[_-]?key\s*[=:]\s*["']?[a-z0-9]{16,}["']?`)},
	{"Generic Token", regexp.MustCompile(`(?i)token\s*[=:]\s*["']?[a-z0-9]{16,}["']?`)},
	{"Generic Secret", regexp.MustCompile(`(?i)secret\s*[=:]\s*["']?[a-z0-9]{16,}["']?`)},
	{"Password", regexp.MustCompile(`(?i)password\s*[=:]\s*["']?[^\s"']{8,}["']?`)},
	{"Private Key", regexp.MustCompile(`-----BEGIN [A-Z ]+PRIVATE KEY-----`)},
	{"GitHub Token", regexp.MustCompile(`ghp_[A-Za-z0-9]{36}`)},
	{"Slack Token", regexp.MustCompile(`xox[baprs]-[A-Za-z0-9-]+`)},
}

// ScanForSecrets scans a file for common credential patterns
// Returns one warning string per matched line, or nil for clean files
func ScanForSecrets(path string) ([]string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	lines := strings.Split(string(data), "\n")
	var warnings []string

	for lineNum, line := range lines {
		for _, pattern := range patterns {
			if pattern.re.MatchString(line) {
				warning := fmt.Sprintf("Line %d: potential secret matched pattern '%s'", lineNum+1, pattern.label)
				warnings = append(warnings, warning)
				break // Only report first match per line
			}
		}
	}

	if len(warnings) == 0 {
		return nil, nil
	}
	return warnings, nil
}
