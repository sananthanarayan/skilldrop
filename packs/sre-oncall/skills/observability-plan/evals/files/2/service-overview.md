# Repeat Prescriptions service: overview

Owner: Digital Pharmacy team, Larkspur Pharmacy (84 branches)

## What it does

Patients request a repeat prescription in the app or on the website. The request goes to the patient's branch, where it is checked against the Dispensary Management System (DMS) and dispensed. When the order is ready, the patient gets an SMS saying it can be collected.

## Journey and components

1. **Request**: app/web front end calls the Refill API.
2. **Check and queue**: Refill API looks up the patient's repeat list in the DMS and puts the order on the branch's dispensing queue.
3. **Dispense**: branch staff work through the queue in the DMS.
4. **Notify**: when staff mark the order ready, the Notifier sends an SMS through our SMS provider.

## Dependencies

- **DMS** is run by an outside supplier. Their contract promises 99.9% monthly availability, and they report it monthly. The Refill API cannot take a request without it; there is no offline mode.
- **SMS provider**: messages are usually delivered within a minute; the provider gives delivery receipts.

## Traffic

About 40,000 refill requests a week, almost all between 07:00 and 22:00. Branches are closed 22:00 to 07:00 and the app shows "requests will be processed in the morning", but requests can still be submitted overnight (typically 0 to 20 an hour).

## What the product owner wants

"I want 99.999% availability on refills. And please add patient ID and prescription ID as labels on every metric so we can debug individual complaints."
