# Voltbay public charger — screen copy (draft v0.3)

Voltbay makes pay-as-you-go electric vehicle chargers installed in council car parks and supermarket car parks. Each unit has a small colour touchscreen and a contactless card reader. The screen is read in daylight, often by someone standing in the rain.

Display limits (from hardware team):
- Buttons: max **16 characters** including spaces.
- Titles: max **28 characters**.
- Body text: max **90 characters**, max 2 lines.

| Screen | Element | Current draft |
|---|---|---|
| S1 Idle | Title | Welcome to your Voltbay charging station |
| S1 Idle | Body | Plug in your vehicle to the pump then tap to begin |
| S1 Idle | Button | Start charging session now |
| S2 Payment | Title | Payment |
| S2 Payment | Body | Tap your card on the reader. Price: £0.45/kWh |
| S2 Payment | Button | Cancel |
| S3 Charging | Title | Charge point active |
| S3 Charging | Body | Your car is charging. kWh delivered and cost so far update live. |
| S3 Charging | Button | Stop |
| S4 Finished | Title | Charging complete |
| S4 Finished | Body | Unplug the cable from the charger. Receipt available. |
| S4 Finished | Button | Get receipt |
| S5 Error | Title | Error |
| S5 Error | Body | (one per error code — see error-codes.csv) |
| S5 Error | Button | OK |
