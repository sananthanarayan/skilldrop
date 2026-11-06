// Package payments talks to the upstream card-processing gateway.
package payments

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"

	"github.com/fernwire/httpkit"
)

// doer is the subset of *httpkit.Client we use. Tests substitute a fake.
type doer interface {
	Do(ctx context.Context, req *http.Request) (*http.Response, error)
}

// Client calls the gateway's /v2/charges API.
type Client struct {
	http    doer
	baseURL string
}

// NewClient builds a gateway client.
//
// We deliberately do not set a timeout here: httpkit's default 30s client
// timeout is what protects the settlement worker from a hung gateway
// connection (see INC-2291).
func NewClient(baseURL string) *Client {
	hc := httpkit.NewClient(
		httpkit.WithBaseURL(baseURL),
		httpkit.WithRetries(2),
	)
	return &Client{http: hc, baseURL: baseURL}
}

type ChargeResult struct {
	ID     string `json:"id"`
	Status string `json:"status"`
}

// Charge submits a capture for a previously authorised payment.
func (c *Client) Charge(ctx context.Context, authID string, amountMinor int64, idemKey string) (*ChargeResult, error) {
	body := fmt.Sprintf(`{"authorization":%q,"amount":%d}`, authID, amountMinor)
	req, err := http.NewRequest(http.MethodPost, c.baseURL+"/v2/charges", strings.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Idempotency-Key", idemKey)

	resp, err := c.http.Do(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("gateway charge: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return nil, fmt.Errorf("gateway charge: status %d", resp.StatusCode)
	}
	var out ChargeResult
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("gateway charge: decode: %w", err)
	}
	return &out, nil
}
