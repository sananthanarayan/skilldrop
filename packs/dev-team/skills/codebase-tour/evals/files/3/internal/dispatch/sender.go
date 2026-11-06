package dispatch

import (
	"bytes"
	"context"
	"fmt"
	"net/http"
)

type Sender interface {
	Send(ctx context.Context, url string, body []byte) error
}

type HTTPSender struct{ client *http.Client }

func NewHTTPSender(c *http.Client) *HTTPSender { return &HTTPSender{client: c} }

func (s *HTTPSender) Send(ctx context.Context, url string, body []byte) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("build request: %w", err)
	}
	resp, err := s.client.Do(req)
	if err != nil {
		return fmt.Errorf("post %s: %w", url, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return fmt.Errorf("post %s: status %d", url, resp.StatusCode)
	}
	return nil
}
