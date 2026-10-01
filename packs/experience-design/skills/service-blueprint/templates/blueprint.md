# Service blueprint: {customer type} {does what}, from {trigger} to {end state}

**Evidence level:** {[observed] / [documented] / [assumption-based]} · **Built on:** {user-journey-map title, or "no journey map"}
**Variants not shown:** {list} · **Assumptions to confirm first:** {list, or "none"}

## Blueprint

| Lane | 1. {step} | 2. {step} | 3. {step} |
|---|---|---|---|
| **Evidence** | {} | {} | {} |
| **Customer actions** | {} | {} | {} |
| *— line of interaction —* | | | |
| **Frontstage** (owner) | {action} ({role}) | | |
| *— line of visibility —* | | | |
| **Backstage** (owner) | {action} ({team}) | | |
| *— line of internal interaction —* | | | |
| **Support processes** | {system / third party} | | |
| **Fail points / waits** | ⚠ {} · ⏱ {duration} | | |

## Diagram

```mermaid
flowchart LR
    subgraph EV["Evidence"]
        direction LR
        e1["{evidence}"]
    end
    subgraph CU["Customer actions"]
        direction LR
        c1["1. {step}"] --> c2["2. {step}"]
    end
    subgraph FR["Frontstage (line of interaction above)"]
        direction LR
        f1["{action}"]
    end
    subgraph BA["Backstage (line of visibility above)"]
        direction LR
        b1["{action}"]
    end
    subgraph SU["Support (line of internal interaction above)"]
        direction LR
        s1["{system}"]
    end
    c1 --- e1
    c1 --> f1
    f1 --> b1
    b1 --> s1
```

## Fail points and waits

| # | Step | Type | What happens | Customer effect | Frequency / duration | Handoff? |
|---|---|---|---|---|---|---|
| 1 | {} | ⚠ fail / ⏱ wait | {} | {} | {measured / SLA / [estimate]} | {team → team} |

## Pain → cause

| Customer pain | Cause (lane, step) |
|---|---|
| {} | {} |

## Ranked fixes

| Rank | Fix (outcome) | Lane it changes | Owner | Addresses |
|---|---|---|---|---|
| 1 | {} | {} | {} | {#} |

**Not prioritised now:** {list}

## Open questions

- {}
