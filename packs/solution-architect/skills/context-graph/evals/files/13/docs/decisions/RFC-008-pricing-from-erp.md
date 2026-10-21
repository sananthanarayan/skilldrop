# RFC-008: Read prices from the Halvorsen ERP

Status: Accepted
Date: 2023-02-07
Author: M. Okafor
Governs: shopfront/pricing/erp_client.py

## Decision
Shopfront reads the current price for a SKU from the Halvorsen ERP `GetItemPrice` SOAP call
through `shopfront/pricing/erp_client.py`. The ERP is the single source of truth for prices.
