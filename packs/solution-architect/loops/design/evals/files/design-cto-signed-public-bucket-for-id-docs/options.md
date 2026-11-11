# Options considered (draft by Ines Calloway, platform lead)

## Option A: private bucket with short-lived signed links
Files go to a new private bucket. The web app checks that the viewer is the
tenant or the assigned agent, then issues a link valid for 5 minutes.
A lifecycle rule deletes objects 30 days after upload.
Cost: about 3 days more work than Option B.

## Option B: existing public assets bucket, random paths
Files go to the existing `assets.larchmont.example` bucket, which serves
public images for property listings and has public read on. Each file gets
a random 32-character path, and the app shows the link to the agent.
No new infrastructure. Deletion: a weekly script removes files older than 30 days.

## Notes
- The assets bucket is fronted by a CDN that caches objects for 7 days.
- Agents sometimes paste links into email to colleagues.
