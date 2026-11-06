# Online resident parking permit renewal: low-emission discount

Riverton Borough Council (invented), Parking Services. Status: approved for build, release planned
for 1 December, before the January renewal rush.

## Background

Residents renew their parking permit online each year. From this release, permits for low-emission
vehicles get a 50% discount on the standard annual price of £120. Emissions are looked up from the
national vehicle register using the registration number the resident enters.

## Acceptance criteria

The seven acceptance criteria below must all pass before release.

- AC1. A resident can start a renewal from 30 days before their permit's expiry date. Before that,
  the renew button is hidden and the page shows the date renewal opens.
- AC2. A permit that expired 60 days ago or less can still be renewed. A permit that expired more
  than 60 days ago cannot be renewed; the resident is sent to the new-application form.
- AC3. The registration number entered is looked up on the vehicle register. If the vehicle's
  CO2 emissions are 50 g/km or less, the low-emission price applies.
- AC4. If the vehicle register lookup fails or times out, the resident is charged the standard
  price and told they can claim the discount by contacting Parking Services.
- AC6. The price shown on the confirmation page is the amount sent to the payment provider.
- AC7. A resident can hold at most one active permit per address. Renewal replaces the old permit;
  it never creates a second one.

## Prices

| Vehicle            | Annual price |
|--------------------|--------------|
| Standard           | £120         |
| Low-emission       | £65          |

## Dependencies and constraints

- Vehicle register: the test environment has a stub only. The live register cannot be called from
  test or staging under the data-sharing agreement.
- Payment provider: unchanged by this release and out of scope; it is tested by the provider.
- Parking Services wants confidence that the site will cope with the January renewal rush.
