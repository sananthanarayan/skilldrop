# Infrastructure as code

Terraform you can hand to another team and plans you can trust before apply: reusable modules with secure defaults, and a plan review that catches destroys, data loss, access widening and drift.

`/plugin install infra-as-code@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Write a module, then review its plan before the first apply

Paste this into Claude Code:

```text
Write a Terraform module for an S3 bucket that stores our access logs for a year. Several teams will call it. Then, once I've run terraform plan on the example, review the plan before I apply.
```

- **Before you start:** A Terraform project or a described piece of infrastructure
- **Before you start:** Terraform installed locally if you want to validate and plan the result
- **How to tell it worked:** terraform-module writes versions.tf, variables.tf, main.tf, outputs.tf, a basic example and a README with inputs and outputs tables, with encryption on and public access off by default. terraform-plan-review returns SAFE TO APPLY, APPLY WITH CARE or DO NOT APPLY with every destroy and replace named.
- **If nothing happens:** If terraform validate fails, paste the error back and ask terraform-module to fix that file. If terraform-plan-review does not activate, ask for it by name ("use terraform-plan-review") and give it the output of terraform show -json tfplan.

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `council-review`
- `doc-critique`
- `output-hygiene`
- `terraform-module`
- `terraform-plan-review`

More: https://sananthanarayan.github.io/skilldrop/packs/infra-as-code/
