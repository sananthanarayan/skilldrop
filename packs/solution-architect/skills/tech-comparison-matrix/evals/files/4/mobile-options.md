# DriverRun app: rewrite or not?

Notes for the decision. Ilse Vandermeer, mobile lead, Varley Parcels, 1 Oct 2026.

## Where we are
- DriverRun is two separate native apps: Android (Kotlin, since 2019) and iOS (Swift, since 2021).
- Every feature gets built twice. iOS is currently 3 features behind Android.
- Options on the table: (A) keep both native apps, (B) rewrite in React Native, (C) rewrite in Flutter.
- My own preference going in is B, since half the team already writes React.

## Who uses it
- 2,650 employed drivers on company handhelds: Orrin H4 (Android 11, 3 GB RAM, built-in barcode scanner)
- 1,150 subcontractor drivers on their own phones: about 700 iPhone, 450 Android
- So about 80% of drivers are on the handheld.

## Must-haves
1. Scan with the H4's built-in scanner (through the Orrin SDK). Camera scanning is too slow for a 140-stop route.
2. The whole route works offline.
3. Proof-of-delivery photo feature live for all drivers by 1 Feb 2027. This is in the Hadleigh Home contract, with a penalty clause.
4. Print to the Bluetooth label printers in the vans.

## Team
- 9 mobile engineers: 4 Android, 3 iOS, 2 who do both.
- 5 of the 9 have shipped React/TypeScript (rotations on the web portal).
- Nobody has shipped Dart. 2 have done a Flutter course.

## Scanner SDK
- Wiki page "Orrin integration" (last edited March 2024 by Stellan, who has since left):
  "Orrin publishes official plugins for both Flutter and React Native, so cross-platform is not a problem."
- Email from Orrin partner support, 9 Sept 2026: "The H4 SDK is distributed as an Android AAR only.
  We do not publish or support React Native or Flutter wrappers. The community Flutter plugin you
  mention was last updated in 2024 and does not support H4 firmware 7. Partners usually write their own bridge."
- Our handhelds are on firmware 7.

## Spike results (August, two weeks each, one engineer)
- React Native prototype: the scan-to-stop-list screen works on the H4 using a bridge we wrote ourselves (4 days). Cold start 2.9 s on the H4.
- Flutter prototype: cold start 2.1 s, measured on a Pixel 8 dev phone. On the H4 the scan screen crashed using the community plugin. Ran out of time, not investigated.
- For reference, today's native Android app cold-starts in 1.8 s on the H4.
- Label printing: not tried in either spike.

## Estimates (the team's, calendar time, starting Mon 2 Nov 2026 after the current release)
- A: proof-of-delivery photo in both native apps: 7 weeks.
- B: React Native rewrite to parity with today's Android app: 26 weeks. Photo feature after that: +3 weeks.
- C: Flutter rewrite to parity: 30 weeks. Photo feature after that: +3 weeks.
- Nobody has estimated what it costs us to keep building everything twice under A.
