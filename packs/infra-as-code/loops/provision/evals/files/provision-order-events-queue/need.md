# Need: order events queue

**Team:** Fulfilment platform, Quillfield Goods (fictional)
**Environment:** prod, eu-west-2, account 111122223333
**Apply approver:** Rui Okafor, platform on-call

## What we need

An SQS queue that receives order-created events from the existing SNS topic
`arn:aws:sns:eu-west-2:111122223333:orders-created`.

- Queue name: `order-events`
- Keep messages for 4 days.
- After 5 failed receives, move the message to a dead-letter queue `order-events-dlq`. Keep DLQ messages for 14 days.
- Visibility timeout 60 seconds (the worker takes up to 40 seconds per message).
- Encrypt both queues with a customer-managed KMS key, rotation on.
- Only the orders-created topic may send to the queue.
- Raw message delivery on the subscription.

## Not in this change

The consumer role (`arn:aws:iam::111122223333:role/fulfilment-worker`) gets its permissions to read the queue in a separate change next week. Nothing in this change should touch it.

## How the module is called

`envs/prod/main.tf`:

```hcl
module "order_events" {
  source           = "../../modules/order-events-queue"
  name             = "order-events"
  source_topic_arn = "arn:aws:sns:eu-west-2:111122223333:orders-created"
  tags = {
    team        = "fulfilment"
    cost-centre = "cc-4410"
  }
}
```

## Plan

Run from `envs/prod`:

```
terraform plan -out=order-events.tfplan
terraform show -json order-events.tfplan > plan.json
```
