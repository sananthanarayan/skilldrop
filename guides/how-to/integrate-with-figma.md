---
title: Use skilldrop with Figma
summary: Connect Figma files to the architecture and diagram skills — generate diagrams for FigJam, produce Figma-ready specs from a design session, or reverse-engineer decisions from a mockup.
kind: how-to
---

# Use skilldrop with Figma

Two integration paths: the `figma-diagrams` skill uses the Figma API directly (requires a token); the other diagram and design skills work from text descriptions you provide.

## Generate diagrams for FigJam

`architecture-diagrams` produces Mermaid or PlantUML syntax. FigJam has a Mermaid plugin that renders these directly:

1. Run `architecture-diagrams` with a system description
2. Copy the Mermaid block from the output
3. In FigJam: Insert → Mermaid → paste the syntax

```
Draw a Mermaid sequence diagram showing the OAuth flow between the browser,
our API gateway, and the identity provider.

Run architecture-diagrams.
```

The resulting diagram stays editable in FigJam and can be linked from the design doc.

## Use the figma-diagrams skill

`figma-diagrams` calls the Figma API directly. It requires `FIGMA_TOKEN` — see [Supply credentials to skills](supply-credentials.md) for how to set it.

```
Inspect the structure of this Figma file: https://figma.com/file/abc123/MyDesign

Run figma-diagrams.
```

The skill returns a structured description of the file's layers, components, and relationships — useful as input for `reverse-architecture` or `design-doc`.

You can also post a comment back to Figma:

```
/figma-diagrams post-comment https://figma.com/file/abc123/MyDesign "Architecture review passed."
```

## Reverse-engineer decisions from a Figma mockup

When a designer hands you a Figma mockup, describe its structure to `reverse-architecture` to document the implied system decisions:

```
Here is the structure of a Figma mockup for our checkout flow:
- Three screens: cart, address, payment
- Each screen has a header component, a form, and a CTA button
- The payment screen has a PCI compliance badge

Run reverse-architecture.
```

The skill returns an ADR or design-doc skeleton capturing the decisions the design implies (state management, API calls, security boundaries).

## Link Figma to a design doc

When running `design-doc`, include the Figma file URL in your input so the output document stays connected to the visual design:

```
System: checkout flow redesign
Figma file: https://figma.com/file/abc123/Checkout-Redesign
[describe the system]

Run design-doc.
```

The skill will reference the Figma link in the document, keeping design and spec in sync.

## Using the Figma MCP

If the Figma MCP is installed in Claude Code, the agent can pull Figma node data directly into context without you copying anything:

```
Fetch the component structure from https://figma.com/file/abc123 and run reverse-architecture.
```

See also: [Use skills with MCP servers](use-with-mcp-servers.md)
