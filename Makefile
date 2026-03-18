.PHONY: build test lint docker-build

build:
	go build -o ./bin/loadout ./cmd/loadout

test:
	go test ./...

lint:
	go vet ./...

docker-build:
	docker build -t loadout:latest .
