# Scope Control Protocol

Use before any write task and before merging worker output. BAGEL continues by default, but not by silently expanding authority.

## Scope Delta

Record each write task:

```yaml
scope_delta:
  allowed_paths: []
  touched_paths: []
  touched_paths_outside_scope: []
  new_dependencies: []
  dependency_scope: dev | runtime | major_framework
  dependency_justification: ""
  architecture_boundary_changed: false
  product_identity_changed: false
  auth_touched: false
  privacy_touched: false
  payment_touched: false
  production_data_touched: false
  data_migration_touched: false
  approval_required: false
  approval_ref: null
  constitutional_court_ref: null
  explicit_contract_ref: null
```

Rules:

- Outside-scope path touches require `approval_ref`.
- New runtime or framework dependencies require justification.
- Product identity changes require Constitutional Court.
- Auth, privacy, payment, production data, or migration touches require explicit contract or hard-stop.

Run:

```bash
python scripts/scope_check.py <project-root>
```
