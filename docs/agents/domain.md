# Domain Docs

Engineering skills should use this repository's domain documentation when exploring or changing code.

## Read before exploring

- `CONTEXT.md` at the repository root, if present.
- Relevant ADRs under `docs/adr/`, if present.

If these files do not exist, proceed silently. Create them only when a domain term or architectural decision needs to be recorded.

## Layout

This is a single-context repository:

```
/
├── CONTEXT.md
├── docs/adr/
└── src/
```

Use terminology defined in `CONTEXT.md` in issues, proposals, tests, and documentation. If planned work conflicts with an ADR, call out the conflict explicitly rather than silently overriding it.
