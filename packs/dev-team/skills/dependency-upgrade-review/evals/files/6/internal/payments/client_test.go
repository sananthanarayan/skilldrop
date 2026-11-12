package payments

import (
	"context"
	"errors"
	"io"
	"net/http"
	"strings"
	"testing"

	"github.com/stretchr/testify/require"
)

type fakeDoer struct {
	status int
	body   string
	err    error
	got    *http.Request
}

func (f *fakeDoer) Do(_ context.Context, req *http.Request) (*http.Response, error) {
	f.got = req
	if f.err != nil {
		return nil, f.err
	}
	return &http.Response{
		StatusCode: f.status,
		Body:       io.NopCloser(strings.NewReader(f.body)),
	}, nil
}

func TestChargeOK(t *testing.T) {
	fd := &fakeDoer{status: 201, body: `{"id":"ch_1","status":"captured"}`}
	c := &Client{http: fd, baseURL: "https://gw.test"}
	res, err := c.Charge(context.Background(), "auth_1", 1250, "idem-1")
	require.NoError(t, err)
	require.Equal(t, "ch_1", res.ID)
	require.Equal(t, "idem-1", fd.got.Header.Get("Idempotency-Key"))
}

func TestChargeGatewayError(t *testing.T) {
	fd := &fakeDoer{err: errors.New("boom")}
	c := &Client{http: fd, baseURL: "https://gw.test"}
	_, err := c.Charge(context.Background(), "auth_1", 1250, "idem-1")
	require.Error(t, err)
}

func TestChargeNon2xx(t *testing.T) {
	fd := &fakeDoer{status: 502, body: ``}
	c := &Client{http: fd, baseURL: "https://gw.test"}
	_, err := c.Charge(context.Background(), "auth_1", 1250, "idem-1")
	require.ErrorContains(t, err, "status 502")
}
