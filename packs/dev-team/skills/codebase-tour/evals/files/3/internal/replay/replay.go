// Package replay re-sends dead-lettered events when an operator asks for it.
package replay

import (
	"context"
	"fmt"
	"time"

	"example.com/tidepool/internal/config"
	"example.com/tidepool/internal/dispatch"
	"example.com/tidepool/internal/store"
)

// Replay sends each dead event again. It keeps its own retry loop so an operator
// replay never blocks on the dispatcher's queue.
func Replay(ctx context.Context, cfg config.Config, q *store.Queries, s dispatch.Sender) error {
	events, err := q.DeadEvents(ctx)
	if err != nil {
		return fmt.Errorf("dead events: %w", err)
	}
	for _, ev := range events {
		for attempt := 1; attempt <= cfg.MaxAttempts; attempt++ {
			if err := s.Send(ctx, ev.EndpointURL, ev.Payload); err == nil {
				_ = q.MarkDelivered(ctx, ev.ID)
				break
			}
			time.Sleep(cfg.RetryDelay)
		}
	}
	return nil
}
