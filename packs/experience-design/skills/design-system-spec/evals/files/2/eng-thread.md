# Thread: dose stepper build questions

**Front-end lead:** Plan is press-and-hold on plus/minus to auto-repeat, accelerating after 1 s. Nurses going from 0.5 to 10 mL would otherwise need 19 taps. I'll build that unless someone objects.

**Clinical safety officer:** Objecting. Our hazard log entry HZ-114 says dose controls must not auto-repeat: an accidental long press on a moving ward cart could jump several steps without the nurse noticing. One tap, one step. Typing is the fast path for big changes.

**Front-end lead:** Noted, but product hasn't signed that off. Leaving hold-to-repeat in the ticket for now.

**Product manager:** Can the spec also say how often nurses currently hit the 10 mL max? Would help justify the range.

**QA:** What should happen if someone types 12, or 0, or 2.3? The drawings don't say.
