package payments

import (
	"context"

	"github.com/quillstack/zlogx"
)

// Pending is a capture waiting to be settled.
type Pending struct {
	AuthID      string
	AmountMinor int64
	IdemKey     string
}

// SettleBatch is run by the nightly settlement worker. It processes captures
// one at a time, in order; a single stuck call blocks the rest of the batch.
func SettleBatch(c *Client, batch []Pending, log *zlogx.Logger) (settled int) {
	for _, p := range batch {
		// No per-call deadline: we rely on the client's own timeout.
		res, err := c.Charge(context.Background(), p.AuthID, p.AmountMinor, p.IdemKey)
		if err != nil {
			log.Warn("settle failed", "auth", p.AuthID, "err", err)
			continue
		}
		log.Info("settled", "auth", p.AuthID, "charge", res.ID)
		settled++
	}
	return settled
}
