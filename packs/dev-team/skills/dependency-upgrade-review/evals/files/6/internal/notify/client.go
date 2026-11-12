// Package notify sends merchant webhooks.
package notify

import (
	"bytes"
	"context"
	"net/http"
	"time"

	"github.com/fernwire/httpkit"
)

type Sender struct {
	hc *httpkit.Client
}

func NewSender() *Sender {
	return &Sender{hc: httpkit.NewClient(
		httpkit.WithTimeout(5*time.Second),
		httpkit.WithRetries(3),
	)}
}

func (s *Sender) Send(ctx context.Context, url string, payload []byte) error {
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(payload))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := s.hc.Do(ctx, req)
	if err != nil {
		return err
	}
	return resp.Body.Close()
}
