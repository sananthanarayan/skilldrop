export interface FeedEvent {
  id: string;
  kind: string;
  occurredAt: string;
  payload: Record<string, unknown>;
}

export interface Invoice {
  id: string;
  customerId: string;
  amountMinor: number;
  currency: string;
}
