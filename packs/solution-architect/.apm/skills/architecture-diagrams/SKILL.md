---
name: architecture-diagrams
description: Generate architecture diagrams (Mermaid, PlantUML, C4) from a written description of a system. Supports AWS/Azure/GCP cloud topologies, microservice landscapes, sequence flows, container diagrams, and ER models. Use whenever the user asks for an architecture diagram, system sketch, flow diagram, or visualization of a design.
---

# architecture-diagrams

You help the user turn a written system description into a clean, renderable architecture diagram.

## How to respond

1. **Clarify only what blocks correctness.** Before drawing, you may ask 1–2 short questions if the description is missing something load-bearing (e.g., "Is auth synchronous or via a sidecar?"). Don't pepper the user with questions for taste preferences — pick a reasonable default and call it out.

2. **Pick the right notation.** Use this rough mapping unless the user requests otherwise:

   | User's intent | Use |
   |---|---|
   | Cloud architecture (AWS/Azure/GCP) — boxes, arrows, services | **Mermaid** `flowchart` or `graph` |
   | Request flow across services / call order matters | **Mermaid** `sequenceDiagram` |
   | Strategic / multi-level view (context → container → component) | **C4 (PlantUML !include c4)** |
   | Data model, tables, relationships | **Mermaid** `erDiagram` |
   | State machine / workflow | **Mermaid** `stateDiagram-v2` |
   | Class / type hierarchy | **Mermaid** `classDiagram` |
   | Looks-pretty UML-style for slides | **PlantUML** |

3. **Output the diagram in a fenced code block** with the correct language tag (` ```mermaid `, ` ```plantuml `). Then add 2–4 bullet points underneath explaining the key design choices ("Why two ECS services and not one?") so the diagram is reviewable, not just renderable.

4. **Offer next steps**, e.g., "Want me to export this as SVG via the Mermaid CLI?" or "Want me to push this into a Figma file? (use the `figma-diagrams` skill)".

## Useful references in this skill

When you need a starting shape, copy from one of the templates rather than inventing notation from scratch — it cuts down on syntax errors and keeps style consistent across diagrams.

- [`templates/mermaid-flowchart.md`](templates/mermaid-flowchart.md) — basic boxes-and-arrows starter
- [`templates/mermaid-sequence.md`](templates/mermaid-sequence.md) — sequenceDiagram with actors and async messages
- [`templates/mermaid-aws.md`](templates/mermaid-aws.md) — AWS-flavoured flowchart using emojis as service icons
- [`templates/c4-container.puml`](templates/c4-container.puml) — C4 container diagram skeleton (PlantUML)

Worked examples to learn from:

- [`examples/aws-three-tier.md`](examples/aws-three-tier.md) — three-tier web app on AWS, Mermaid flowchart
- [`examples/microservices-sequence.md`](examples/microservices-sequence.md) — order-placement flow across 4 services
- [`examples/c4-container-saas.md`](examples/c4-container-saas.md) — SaaS app, C4 container level

## Quality bar

A good diagram from this skill should:

- **Fit on one screen.** If you have more than ~15 nodes, split into two diagrams (e.g., "Context" and "Container") rather than cramming everything in.
- **Show direction of data flow,** not just connections. Arrows should mean something.
- **Label every arrow** that crosses a trust boundary or a network hop.
- **Use subgraphs / groups** to make zones explicit (VPC, public/private subnets, account boundaries, on-prem vs cloud).
- **Be valid syntax.** Mentally trace through the Mermaid/PlantUML once before responding. Common breakers: unescaped `(` `)` `<` `>` inside labels, missing `end` for subgraphs, mixing graph types.

## What this skill does NOT do

- It doesn't render to PNG/SVG itself. To render, suggest the user use the Mermaid Live Editor (https://mermaid.live), the Mermaid CLI (`mmdc`), or the VS Code Mermaid preview.
- It doesn't push to Figma directly. For that, hand off to the [`figma-diagrams`](../figma-diagrams/SKILL.md) skill.
- It doesn't generate Visio/Lucid native files.

## Anti-patterns to avoid

- ❌ Inventing service names ("ServiceA", "ServiceB"). Use the user's vocabulary or ask.
- ❌ Putting every box at the top level. Group by concern.
- ❌ Mermaid flowchart with 30+ nodes — split it.
- ❌ Using a sequence diagram when the user asked "what does the system look like" — that's a structural question, use a flowchart or C4.
