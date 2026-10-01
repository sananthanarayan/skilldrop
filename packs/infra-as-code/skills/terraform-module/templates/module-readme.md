# <module-name>

<One or two sentences: what this module creates and what it is for. Name the secure defaults a caller gets without setting anything.>

## Usage

```hcl
module "<instance-name>" {
  source = "<registry, git or relative path>"

  <required_input> = <placeholder value>

  tags = {
    "environment" = "<env>"
    "owner"       = "<team>"
  }
}
```

A runnable version is in `examples/basic`.

## What it creates

| Resource | Why |
|---|---|
| `<type>.<name>` | <the job it does, and the secure setting it carries> |

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `<name>` | `<type>` | (required) or `<default>` | <what the caller decides, and the valid range> |
| `tags` | `map(string)` | `{}` | Extra tags, merged over the module defaults |

## Outputs

| Name | Description |
|---|---|
| `<name>` | <what a caller uses it for> |

## Notes

- <Any opt-in variable that weakens a default, and what it opens.>
- <Where account or project IDs come from: a data source, never a literal.>
- This module does not configure a provider or backend. The caller sets region, credentials and state.

## Before you apply

```bash
terraform fmt -recursive
terraform init -backend=false && terraform validate
terraform plan   # from examples/basic, against a sandbox
```

Run `tflint` and `checkov -d .` too if your team uses them.
