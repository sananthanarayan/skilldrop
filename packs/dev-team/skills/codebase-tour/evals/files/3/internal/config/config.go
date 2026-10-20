package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

type Config struct {
	DatabaseURL string
	MaxAttempts int
	RetryDelay  time.Duration
}

// FromEnv reads every setting from the environment. There is no config file.
func FromEnv() (Config, error) {
	cfg := Config{MaxAttempts: 5, RetryDelay: 2 * time.Second}
	cfg.DatabaseURL = os.Getenv("TIDEPOOL_DATABASE_URL")
	if cfg.DatabaseURL == "" {
		return cfg, fmt.Errorf("TIDEPOOL_DATABASE_URL is required")
	}
	if v, ok := os.LookupEnv("TIDEPOOL_MAX_ATTEMPTS"); ok {
		n, err := strconv.Atoi(v)
		if err != nil {
			return cfg, fmt.Errorf("TIDEPOOL_MAX_ATTEMPTS: %w", err)
		}
		cfg.MaxAttempts = n
	}
	if v, ok := os.LookupEnv("TIDEPOOL_RETRY_DELAY"); ok {
		d, err := time.ParseDuration(v)
		if err != nil {
			return cfg, fmt.Errorf("TIDEPOOL_RETRY_DELAY: %w", err)
		}
		cfg.RetryDelay = d
	}
	return cfg, nil
}
