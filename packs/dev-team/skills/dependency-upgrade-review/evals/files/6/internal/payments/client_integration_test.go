//go:build integration

package payments

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/require"
)

// TestChargeHungGatewayTimesOut guards INC-2291: a gateway that accepts the
// connection and never responds must not block the settlement worker forever.
func TestChargeHungGatewayTimesOut(t *testing.T) {
	block := make(chan struct{})
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		<-block
	}))
	defer srv.Close()
	defer close(block)

	c := NewClient(srv.URL)
	done := make(chan error, 1)
	go func() {
		_, err := c.Charge(context.Background(), "auth_1", 100, "idem-hang")
		done <- err
	}()

	select {
	case err := <-done:
		require.Error(t, err)
	case <-time.After(2 * time.Minute):
		t.Fatal("Charge did not time out against a hung gateway")
	}
}
