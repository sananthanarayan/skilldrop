# Northgate Grocers loyalty app: launch note

Launch: Monday 9 November 2026 (iOS and Android, UK only)
Risk owner for the launch: Priya Venkataraman, Director of Digital (on leave 2 to 20 November)
Product lead: Dev Ostrowski
Security lead: Ines Carvalho

## What the app does

- Customers sign up with email and password and collect points by scanning the QR code on
  their till receipt.
- When a customer is within 200 m of a Northgate store, the app shows a push notification
  with that store's offers. This uses the phone's precise location. The current build asks
  for "Allow all the time" location permission so it can notify in the background.
- Marketing added the Beacon analytics SDK (beacon-analytics.example) in October to track
  funnels. It's initialised at app start, before the consent screen.

## Data

Name, email, password hash, points balance, purchase history from scanned receipts,
precise device location, device ID, push token. About 120,000 sign-ups expected in the
first three months.

## Paperwork

- Risk register: attached (risk-register.csv). Last full review was in June, before the
  location feature and the analytics SDK were added; R2, R4 and R5 were refreshed on
  20 October.
- DPIA: none yet. Our DPO (Faye Mbatha) asked in September whether one was needed for the
  location feature; nobody replied.
- Beacon analytics: no data processing agreement on file.
