.PHONY: build test test-integration generate lint

build:
	go build -o bin/tidepool ./cmd/tidepool

test:
	go test ./...

test-integration:
	go test -tags=integration ./internal/store/...

generate:
	sqlc generate

lint:
	golangci-lint run
