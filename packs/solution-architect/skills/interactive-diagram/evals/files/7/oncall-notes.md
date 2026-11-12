# INC-0412 - arrival boards frozen - my notes

Sat 10 Oct, on call for transit-data. All times below are local (CDT).

- 10:41pm  night supervisor at Central Station called. Arrival boards showing the same times "for a couple of hours at least". Asked them to open an incident so it pages properly.
- 10:46pm  acked the page.
- 10:58pm  on VPN. feed-builder says it has been serving last-known positions since about 7pm. Vehicle count looks normal (~210) but the positions aren't moving, which is why nothing looked wrong. Freshness panel in Grafana says OK?? The FeedStale alert never fired.
- ~11:10pm?  restarted avl-ingest on the ingest box (`systemctl restart avl-ingest`). Didn't write the time down, could have been 11:05 or as late as 11:15. The ingest box doesn't ship logs to the central log so I can't check.
- 11:14pm  supervisor says the Central Station boards are moving again.
- 11:30pm  rolled feed-builder back to 3.13.2 anyway. 3.14.0 went out just before all this started and I didn't want to risk it overnight.
- 12:05am  posted all-clear in #ops-transit and resolved the incident.

Open questions for the review:
- why didn't FeedStale fire? (it checks feed age, but we were re-publishing old positions with a fresh timestamp?)
- was it 3.14.0 or did avl-ingest just hang? not sure yet.
- ask Track Ops if the Riverside tram boards were affected too.
