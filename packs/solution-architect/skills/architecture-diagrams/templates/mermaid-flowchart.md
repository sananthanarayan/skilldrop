# Mermaid flowchart starter

Use for: boxes-and-arrows structural diagrams. Top-down (`TD`) reads like a deployment stack; left-right (`LR`) reads like a request flow.

```mermaid
flowchart LR
    User([User])

    subgraph Edge["Edge"]
        CDN[CDN]
        WAF[WAF]
    end

    subgraph App["App tier"]
        LB[Load balancer]
        Web1[Web server 1]
        Web2[Web server 2]
    end

    subgraph Data["Data tier"]
        DB[(Primary DB)]
        Cache[(Cache)]
    end

    User --> CDN --> WAF --> LB
    LB --> Web1 & Web2
    Web1 & Web2 --> Cache
    Web1 & Web2 --> DB
```

## Tips

- `[Box]` rectangle · `([Stadium])` user/external · `[(Cylinder)]` database · `{Diamond}` decision · `>Flag]` event
- Use `&` to fan-out from one source to many destinations: `LB --> Web1 & Web2 & Web3`
- Use `subgraph Name["Display label"]` to draw zones (VPC, account, region)
- Annotate links with `--label-->` to name the arrow
- Pick *one* direction (`TD`, `LR`) per diagram; mixing kills readability
