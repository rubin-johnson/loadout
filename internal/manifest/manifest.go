package manifest

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"

	"gopkg.in/yaml.v3"
)

// RequiredFields lists the required fields for manifest validation
var RequiredFields = []string{"name", "version", "author", "description", "targets"}

// semverRE validates semantic version format
var semverRE = regexp.MustCompile(`^\d+\.\d+\.\d+$`)

// TargetEntry represents a target in the manifest
type TargetEntry struct {
	// Add fields as needed based on the actual structure
}

// Manifest represents the structure of manifest.yaml
type Manifest struct {
	Name        string        `yaml:"name"`
	Version     string        `yaml:"version"`
	Author      string        `yaml:"author"`
	Description string        `yaml:"description"`
	Targets     []TargetEntry `yaml:"targets"`
}

// ManifestError represents validation errors in manifest loading
type ManifestError struct {
	Message string
}

func (e *ManifestError) Error() string {
	return e.Message
}

// Load reads and validates manifest.yaml from the given bundle directory
func Load(bundleDir string) (*Manifest, error) {
	manifestPath := filepath.Join(bundleDir, "manifest.yaml")
	
	// Read the file
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return nil, err
	}
	
	// Unmarshal into map first for validation
	var rawData map[string]any
	if err := yaml.Unmarshal(data, &rawData); err != nil {
		return nil, err
	}
	
	// Create manifest from map
	return fromMap(rawData)
}

// fromMap creates a Manifest from a map with validation
func fromMap(data map[string]any) (*Manifest, error) {
	// Check required fields
	for _, field := range RequiredFields {
		if _, exists := data[field]; !exists {
			return nil, &ManifestError{Message: fmt.Sprintf("missing required field: %s", field)}
		}
	}
	
	// Extract and validate version
	version, ok := data["version"].(string)
	if !ok {
		return nil, &ManifestError{Message: "version must be a string"}
	}
	if !semverRE.MatchString(version) {
		return nil, &ManifestError{Message: "version must be valid semver (x.y.z)"}
	}
	
	// Extract other required fields
	name, ok := data["name"].(string)
	if !ok {
		return nil, &ManifestError{Message: "name must be a string"}
	}
	
	author, ok := data["author"].(string)
	if !ok {
		return nil, &ManifestError{Message: "author must be a string"}
	}
	
	description, ok := data["description"].(string)
	if !ok {
		return nil, &ManifestError{Message: "description must be a string"}
	}
	
	// Handle targets - can be empty slice
	var targets []TargetEntry
	if targetsData, exists := data["targets"]; exists {
		if targetsSlice, ok := targetsData.([]any); ok {
			// Convert to TargetEntry slice if needed
			targets = make([]TargetEntry, len(targetsSlice))
			// For now, just create empty entries
			for i := range targetsSlice {
				targets[i] = TargetEntry{}
			}
		} else {
			return nil, &ManifestError{Message: "targets must be an array"}
		}
	}
	
	return &Manifest{
		Name:        name,
		Version:     version,
		Author:      author,
		Description: description,
		Targets:     targets,
	}, nil
}

// ToMap returns a serialization-ready map representation of the manifest
func (m *Manifest) ToMap() map[string]any {
	return map[string]any{
		"name":        m.Name,
		"version":     m.Version,
		"author":      m.Author,
		"description": m.Description,
		"targets":     m.Targets,
	}
}
