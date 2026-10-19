---
name: interactive-diagram
description: Turn a codebase, a system description, a process or a database schema into one self-contained interactive HTML diagram (architecture, workflow, data flow, lifecycle, ERD or sequence) where every box and arrow cites the file and line or the words it came from, anything inferred is drawn dashed as an assumption, and each cited line is checked against the repository before the page is written. Laid out automatically, opens offline with no CDN, and exports SVG, PNG and Mermaid. Use when the user asks to "visualize", "map" or "make an interactive diagram of" a repo, a request path, a pipeline, an approval process or a set of tables, or wants a diagram they can click through and share as one file.
---

# interactive-diagram

**The rule: nothing goes on the map that the material doesn't show.** A diagram is trusted
more than prose, so an invented box misleads more than an invented sentence. Asked to draw a
repo, the agent's habit is to draw the system such repos usually have: a load balancer, an
auth service, the Kafka the README says is planned. Here every part and every connection
either cites where it came from (`src/api.py:40-52`, or the person's own words) or is drawn
dashed and listed as an assumption. The script checks each cited file and line before it
writes the page, and refuses a spec that cites a line that isn't there.

Two things follow:

- **One question per map.** Draw what answers the question asked ("what happens when an order
  is placed"), not every module in the repo. A part that doesn't help answer it stays off,
  and the reply says in one line what was left out.
- **You write the meaning; the script does the layout.** Never write coordinates. List the
  parts and connections in the order a reader meets them, and the script places them, routes
  every arrow around the boxes, and draws groups as boxes that don't overlap.

## How to respond

1. **Name the question and pick the type.** One sentence: what will the reader understand
   after looking? Then the type:

   | Type | For |
   |---|---|
   | `architecture` | What a system is made of and what talks to what |
   | `dataflow` | Where data or money or documents go, stage by stage |
   | `workflow` | A process with steps, decisions and hand-offs, technical or everyday |
   | `lifecycle` | The states something moves through and what moves it |
   | `erd` | Tables, their columns and keys, and how they reference each other |
   | `sequence` | Who calls whom, in order, for one request or exchange |

2. **Gather the facts, with where each came from.**
   - **A repository:** trace the one path the question is about. Read the entry point, follow
     the calls, and for each part and each arrow note the file and lines that show it. Add a
     few characters from those lines after `#` (`src/api.py:12#stripe.PaymentIntent`) so a
     wrong line number is caught. Config and README files show intent, not behaviour: a
     service the README mentions but no code calls is left off, or drawn as an assumption with
     the README as its only evidence and said so in the reply.
   - **A description:** cite the person's words: `"user: anything over ten days goes to HR"`.
   - **Something you believe but can't point to** (who calls the API, what the worker does
     next): `"assumed": true`. It is drawn dashed and listed. Leave it off if it doesn't help
     answer the question.

3. **Write the spec** as JSON next to where the page will go. The full shape, every kind and
   the ERD and sequence fields are in [`reference.md`](reference.md). The essentials:

   ```json
   {"type": "architecture", "title": "What a checkout request touches",
    "question": "What happens when a shopper checks out?",
    "summary": "One or two sentences: the takeaway a reader should leave with.",
    "groups": [{"id": "vpc", "label": "Private VPC"}],
    "nodes": [{"id": "api", "label": "Checkout API", "kind": "service", "group": "vpc",
               "note": "FastAPI", "evidence": ["src/api.py:8-14#def checkout"]}],
    "edges": [{"from": "api", "to": "db", "label": "insert order", "evidence": ["src/api.py:13"]}],
    "story": [{"text": "The API checks the cache first.", "edges": ["e2"]}]}
   ```

   Labels are a few words; detail goes in `note` (shown on the box) or `detail` (shown when
   clicked). Add a `story` of three to seven steps when the map has a main path worth walking.

4. **Build it.** With a repository, always pass `--repo-root` so the citations are checked:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/build_diagram.py" diagram.json -o diagram.html --repo-root .
   # Other IDEs (from the skill folder)
   python3 scripts/build_diagram.py diagram.json -o diagram.html --repo-root .
   ```

   Errors list the item, what is wrong and the fix, and nothing is written until they're gone.
   Fix the spec, never the evidence: a citation the check can't find is wrong, so find the
   right lines or mark the item assumed. Add `--mermaid diagram.mmd` for a version to paste
   into a README, and `--compare old.json` to show what a change adds, removes and alters.

5. **Reply with the map first.** The first line is the link to the HTML file and what it
   shows. Then the takeaway in one or two sentences, then one line each for what is drawn as
   an assumption and what was left out, and last how many citations were checked. Keep the
   spec beside the page so the map can be rebuilt after the code changes. No recap of
   commands or layout.

6. **When the script can't run** (no `python3`), give the Mermaid version in the reply, with
   assumptions marked, and say that the interactive page needs Python 3.

This is a non-interactive skill: don't stop to ask. With too little to draw from, draw what
you have, mark the rest as assumptions, and say in the reply what would settle them.

**Sharing:** the page shows the cited lines when a part is clicked. Files that hold secrets
(`.env`, keys, credential files) are never shown and secret-looking lines are masked, but
don't cite them in the first place, and read the page before it leaves the team.

## Quality bar

- **Every part and connection cites its source or is drawn as an assumption.** No exceptions
  for the "obvious" ones.
- **Every file citation was checked** against the repository, with the count in the reply.
- **Nothing on the map comes only from a README, a plan or what such systems usually have.**
- **The map answers one stated question,** and what was left out is said.
- **One HTML file that works offline:** no CDN, no external fonts, no network requests.
- **The reply opens with the link and the takeaway,** not with how it was made.

## When to use this skill

- ✅ "Map what happens when an order is placed in this repo, as something I can click through"
- ✅ "Turn this description of our approval process into an interactive flowchart for the team"
- ✅ "Give me an interactive ERD of schema.sql"
- ✅ "Show what this branch changes in the architecture" (two specs and `--compare`)

## When NOT to use this skill

- ❌ A Mermaid, PlantUML or C4 diagram to paste into a doc — use `architecture-diagrams`
- ❌ An as-is architecture write-up in C4 levels from infrastructure files — use `reverse-architecture`
- ❌ Fixing or rendering an existing Mermaid diagram — use `mermaid-render`
- ❌ Charts of numbers, dashboards or metrics — this draws structure, not data

## Anti-patterns to avoid

- ❌ **The usual architecture.** A load balancer, CDN or auth service drawn because systems
  like this have one.
- ❌ **README as evidence of behaviour.** "We use Kafka" in a README is a plan until code
  calls it.
- ❌ **Deleting evidence to pass the check.** A failed citation means the line is wrong or
  the part is an assumption.
- ❌ **Everything in the repo.** Forty boxes answer no question.
- ❌ **Hand-placed coordinates** or a hand-written SVG instead of the script.
- ❌ **A page that loads a library from a CDN.** It breaks offline and leaks the viewer's IP.
