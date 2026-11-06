# Order queue runbook

The `orders-in` queue feeds the fulfilment workers. Rota: **fulfilment-oncall**.

> **Warning:** Purging the queue deletes orders. Never purge without the fulfilment lead.

## Check the backlog

![Queue depth panel](img/queue-depth.png)

1. Read the depth:

   ```bash
   qctl depth orders-in
   ```

2. If it is above 2,000 for 10 minutes, scale the workers to 6.

## Scale back down

Once depth is under 200, scale the workers back to 3.
