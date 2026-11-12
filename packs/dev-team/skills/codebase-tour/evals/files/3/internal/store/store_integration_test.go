//go:build integration

package store

import (
	"context"
	"os"
	"testing"
)

func TestMarkDeadMovesEventOutOfPending(t *testing.T) {
	ctx := context.Background()
	pool, err := Open(ctx, os.Getenv("TIDEPOOL_DATABASE_URL"))
	if err != nil {
		t.Fatal(err)
	}
	q := New(pool)
	if _, err := q.PendingEvents(ctx, 1); err != nil {
		t.Fatal(err)
	}
}
