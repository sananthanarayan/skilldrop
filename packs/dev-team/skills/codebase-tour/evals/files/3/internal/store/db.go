package store

import (
	"context"

	"github.com/jackc/pgx/v5/pgxpool"
)

type Queries struct{ pool *pgxpool.Pool }

func Open(ctx context.Context, url string) (*pgxpool.Pool, error) { return pgxpool.New(ctx, url) }

func New(pool *pgxpool.Pool) *Queries { return &Queries{pool: pool} }

func (q *Queries) list(ctx context.Context, sql string, args ...any) ([]Event, error) {
	rows, err := q.pool.Query(ctx, sql, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Event
	for rows.Next() {
		var e Event
		if err := rows.Scan(&e.ID, &e.EndpointURL, &e.Payload); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, rows.Err()
}

func (q *Queries) exec(ctx context.Context, sql string, args ...any) error {
	_, err := q.pool.Exec(ctx, sql, args...)
	return err
}
