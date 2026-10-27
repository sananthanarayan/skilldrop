# Moorbank District Council — Resident Parking Permits Online (design v1.2)

## Summary
Residents apply for a parking permit online, upload proof of address, pay, and receive a virtual permit tied to their number plate. Civil enforcement officers check plates with handheld devices.

## Components
- Permits web app (council cloud tenancy), on the public internet. Residents log in with email address and password.
- Uploads bucket: proof-of-address documents (council tax bill, tenancy agreement, utility bill) uploaded by residents.
- Permits database: residents' names, addresses, number plates and permit status.
- Payment: hosted payment page from the council's payment provider. The provider itself is out of scope for this review — it is PCI-certified and assessed separately.
- Payment callback: after payment, the provider calls POST /payments/callback on the web app with the permit ID and status=paid; the web app marks the permit active.
- Plates sync API: GET /plates returns all active permit plates for a zone. Enforcement handhelds call it every 15 minutes.
- Back-office: council permit officers review the uploaded documents and approve or reject applications.

## Security notes
- Uploaded documents are virus-scanned before anyone can see them.
- The plates sync API needs no authentication because the handhelds are on the internal network.

## Data flows
1. Resident -> web app (HTTPS) -> uploads bucket. The bucket serves files to the back-office through the council CDN using public-read object URLs, so officers' browsers can open them quickly.
2. A scanning job runs nightly at 01:00 and moves infected files to quarantine.
3. Handhelds connect over the enforcement contractor's 4G SIMs to GET /plates on the web app's public endpoint.
4. Payment provider -> POST /payments/callback.
