package dispatch

import (
	"context"
	"errors"
	"testing"
	"time"

	"example.com/tidepool/internal/config"
	"example.com/tidepool/internal/store"
)

type flakySender struct{ failures, calls int }

func (f *flakySender) Send(context.Context, string, []byte) error {
	f.calls++
	if f.calls <= f.failures {
		return errors.New("boom")
	}
	return nil
}

func TestDeliverRetriesUntilSuccess(t *testing.T) {
	var slept []time.Duration
	s := &flakySender{failures: 2}
	d := &Dispatcher{cfg: config.Config{MaxAttempts: 5, RetryDelay: time.Second}, sender: s,
		sleep: func(t time.Duration) { slept = append(slept, t) }}
	if err := d.Deliver(context.Background(), store.Event{ID: 1}); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if s.calls != 3 || len(slept) != 2 {
		t.Fatalf("calls=%d slept=%v", s.calls, slept)
	}
}

func TestDeliverGivesUpAtMaxAttempts(t *testing.T) {
	s := &flakySender{failures: 10}
	d := &Dispatcher{cfg: config.Config{MaxAttempts: 3}, sender: s, sleep: func(time.Duration) {}}
	if err := d.Deliver(context.Background(), store.Event{ID: 7}); err == nil || s.calls != 3 {
		t.Fatalf("err=%v calls=%d", err, s.calls)
	}
}
