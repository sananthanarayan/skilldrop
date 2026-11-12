# Vellmoor Ferries — online vehicle booking and ramp scanning (brief v0.3)

## What we're building
Passengers book a vehicle space on a sailing online and get a QR boarding pass. At the port, ramp staff scan the QR code on a handheld before the vehicle drives on.

3 routes, 5 ports. 22 sailings a day in summer, 9 in winter. The largest vessel carries 140 cars.

## From the product manager
- "It has to be up 100% of the time — if it's down we can't load the ship."
- "Peak is about 2,000 bookings a day on summer Saturdays, so we need to handle 500 requests per second."
- "Accessibility isn't really relevant, it's a booking site."
- "Keep passenger details forever — marketing want them."

## From operations
- The mobile signal at Harrick pier and Saltness slipway drops out for minutes at a time. Ramp staff can't wait for a signal to load a vehicle.
- Summer bookings open on 1 March at 09:00. Last year 6,000 bookings were made in the first hour, and the old site fell over at 09:04.
- Passengers who need an accessible space (blue-badge holders, wheelchair users) must be able to say so when booking, so the crew can park their vehicle near the lift.

## From legal
- Passenger manifests must be kept for 3 years for the maritime regulator, then deleted.
- Using contact details for marketing needs the passenger's opt-in.
