package dispatch

import (
	"context"
	"fmt"
	"time"

	"example.com/tidepool/internal/config"
	"example.com/tidepool/internal/store"
)

type Dispatcher struct {
	cfg    config.Config
	q      *store.Queries
	sender Sender
	sleep  func(time.Duration)
}

func New(cfg config.Config, q *store.Queries, s Sender) *Dispatcher {
	return &Dispatcher{cfg: cfg, q: q, sender: s, sleep: time.Sleep}
}

// Deliver posts one event, retrying with a fixed delay until MaxAttempts.
func (d *Dispatcher) Deliver(ctx context.Context, ev store.Event) error {
	var last error
	for attempt := 1; attempt <= d.cfg.MaxAttempts; attempt++ {
		if last = d.sender.Send(ctx, ev.EndpointURL, ev.Payload); last == nil {
			return nil
		}
		if attempt < d.cfg.MaxAttempts {
			d.sleep(d.cfg.RetryDelay)
		}
	}
	return fmt.Errorf("event %d: gave up after %d attempts: %w", ev.ID, d.cfg.MaxAttempts, last)
}

func (d *Dispatcher) Run(ctx context.Context) error {
	for {
		events, err := d.q.PendingEvents(ctx, 100)
		if err != nil {
			return fmt.Errorf("pending events: %w", err)
		}
		for _, ev := range events {
			if err := d.Deliver(ctx, ev); err != nil {
				_ = d.q.MarkDead(ctx, ev.ID)
				continue
			}
			_ = d.q.MarkDelivered(ctx, ev.ID)
		}
		d.sleep(time.Second)
	}
}
