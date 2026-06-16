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

- Outside-scope path touches require `approval_ref`; `approval_required: false` cannot waive this.
- `allowed_paths` is mandatory for every write action and must use normalized relative paths.
- Validators derive touched paths from `git diff --name-only <git_ref_start> HEAD` plus untracked files when `git_ref_start` is available; self-reported `touched_paths_outside_scope` must match derived scope.
- New runtime or framework dependencies require justification.
- Product identity changes require Constitutional Court.
- Auth, privacy, payment, production data, or migration touches require explicit contract or hard-stop.
- **risk_level derivation (not pure self-report):** the expert_decision `risk_level` must be consistent with `risk_basis.affected_surfaces` and `reversibility`. If `scope_delta` touches auth/privacy/payment/production_data/user_identity/legal/financial surfaces, `risk_level` must be `high` or `critical`. If `reversibility` is `costly` or `irreversible`, `risk_level` cannot be `low`. `identity_or_scope_change` decisions require `high`/`critical`. `expert_strategy_check.py` enforces these derived rules so a Principal Expert cannot under-rate a sensitive direction to skip the Risk Officer.

Run:

```bash
python scripts/scope_check.py <project-root>
```
