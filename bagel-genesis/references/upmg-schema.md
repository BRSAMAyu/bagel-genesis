# UPMG Schema

The Unified Product Meta-Graph is an optional graph backend for complex software/product runs. Use it only when `.bagel/schema-registry.yaml` selects UPMG. Otherwise the canonical state is the file-backed model described in `references/governance-data-model.md`.

## Database Schema

```sql
-- SQLite schema for UPMG

CREATE TABLE nodes (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,  -- belief, journey, interaction, architecture, contract, verification, implementation
  maturity TEXT NOT NULL,  -- draft, tentative, committed, frozen
  version INTEGER DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  data JSON NOT NULL,
  parent_beliefs JSON,
  child_implementations JSON,
  contracts JSON,
  verifications JSON,
  coherence_constraints JSON,
  uncertainty_vector JSON
);

CREATE TABLE edges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id TEXT NOT NULL,
  target_id TEXT NOT NULL,
  edge_type TEXT NOT NULL,  -- parent_child, implements, verifies, depends_on, constrains
  weight REAL DEFAULT 1.0,
  created_at TEXT NOT NULL,
  FOREIGN KEY (source_id) REFERENCES nodes(id),
  FOREIGN KEY (target_id) REFERENCES nodes(id)
);

CREATE TABLE transactions (
  tx_id TEXT PRIMARY KEY,
  timestamp TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  based_on_snapshot INTEGER NOT NULL,
  operations JSON NOT NULL,
  status TEXT NOT NULL,  -- pending, committed, failed
  commit_hash TEXT
);

CREATE TABLE snapshots (
  version INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  tx_id TEXT NOT NULL,
  node_count INTEGER,
  edge_count INTEGER
);

CREATE INDEX idx_nodes_type ON nodes(type);
CREATE INDEX idx_nodes_maturity ON nodes(maturity);
CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
```

## Node Types

### belief
Product beliefs from constitution.
```json
{
  "id": "PB-LOW-COGNITIVE-LOAD",
  "type": "belief",
  "data": {
    "statement": "First-time users should not feel overwhelmed",
    "source": "constitution.json:target_users.primary"
  }
}
```

### journey
User journey states.
```json
{
  "id": "JOURNEY-FIRST-REFLECTION",
  "type": "journey",
  "data": {
    "name": "First Reflection",
    "entry_point": "/onboarding",
    "exit_condition": "reflection_saved"
  }
}
```

### interaction
UI interaction points.
```json
{
  "id": "UI-FIRST-ENTRY-001",
  "type": "interaction",
  "data": {
    "route": "/onboarding",
    "primary_action": "Get Started",
    "coherence_constraints": ["HG-ACTION-DENSITY-001"]
  }
}
```

### architecture
System components.
```json
{
  "id": "ARCH-AUTH-MIDDLEWARE",
  "type": "architecture",
  "data": {
    "name": "Auth Middleware",
    "module": "src/middleware/auth.ts",
    "responsibilities": ["verify_token", "load_user"]
  }
}
```

### contract
Typed API/data contracts.
```json
{
  "id": "CONTRACT-REFLECTION-001",
  "type": "contract",
  "data": {
    "schema_file": ".bagel/contracts/reflection.ts",
    "endpoints": ["POST /api/reflections", "GET /api/reflections/:id"]
  }
}
```

### verification
Test/simulation specs.
```json
{
  "id": "VERIFY-FIRST-REFLECTION-E2E",
  "type": "verification",
  "data": {
    "test_file": "tests/e2e/first_reflection.spec.ts",
    "coverage": ["UI-FIRST-ENTRY-001", "CONTRACT-REFLECTION-001"]
  }
}
```

### implementation
Source code files.
```json
{
  "id": "IMPL-ONBOARDING-PAGE",
  "type": "implementation",
  "data": {
    "file_path": "src/app/onboarding/page.tsx",
    "lines_of_code": 245
  }
}
```

## Edge Types

### parent_child
Hierarchical relationship.
```sql
INSERT INTO edges (source_id, target_id, edge_type) VALUES
  ('PB-LOW-COGNITIVE-LOAD', 'UI-FIRST-ENTRY-001', 'parent_child');
```

### implements
Implementation fulfills a belief/spec.
```sql
INSERT INTO edges (source_id, target_id, edge_type) VALUES
  ('IMPL-ONBOARDING-PAGE', 'UI-FIRST-ENTRY-001', 'implements');
```

### verifies
Test verifies a node.
```sql
INSERT INTO edges (source_id, target_id, edge_type) VALUES
  ('VERIFY-FIRST-REFLECTION-E2E', 'JOURNEY-FIRST-REFLECTION', 'verifies');
```

### depends_on
Functional dependency.
```sql
INSERT INTO edges (source_id, target_id, edge_type) VALUES
  ('IMPL-ONBOARDING-PAGE', 'ARCH-AUTH-MIDDLEWARE', 'depends_on');
```

### constrains
Coherence rule applies.
```sql
INSERT INTO edges (source_id, target_id, edge_type) VALUES
  ('HG-ACTION-DENSITY-001', 'UI-FIRST-ENTRY-001', 'constrains');
```

## Maturity Levels

### draft
- Initial creation
- Can be freely modified
- No commit requirements

### tentative
- Has been reviewed
- Modifications tracked
- Clearing needed for breaking changes

### committed
- Locked-in decision
- Mutations require immediate clearing
- Constitutional Court review for major changes

### frozen
- Cannot be modified without amendment
- Requires Constitutional Court approval
- Used for north star, core value

## Concurrency Model

```
single-writer transaction log
+ concurrent snapshot reads
+ optimistic validation on commit
```

### Transaction Procedure

```python
# Begin transaction
tx_id = "TX-2026-00129"
snapshot_version = get_current_snapshot_version()
touched_nodes = []

# Read nodes (no locks)
node_a = read_node("UI-FIRST-ENTRY-001")

# Modify locally
node_a.data["primary_action"] = "Begin"

# Begin commit
begin_commit(tx_id, snapshot_version)

# Validate
for node_id in touched_nodes:
    if node_committed_since(node_id, snapshot_version):
        raise StaleSnapshotError

# Write
write_node(node_a)
log_transaction(tx_id, snapshot_version, touched_nodes)

# Commit
commit_transaction(tx_id)
```

## Conflict Resolution

| Conflict Type | Resolution |
|--------------|-----------|
| draft vs draft | Auto rebase if non-overlapping |
| tentative vs tentative | Merge proposal required |
| committed conflict | Atomic rework sandbox |
| frozen conflict | Constitutional checkpoint |

## Initial Seeding

On S4 initialization, seed:
- All belief nodes from constitution
- All journey nodes from user flows
- All architecture nodes from skeleton plan
- All contract nodes from stubs
- All verification nodes from coherence rules

## Query Examples

### Get all beliefs for a journey

```sql
WITH RECURSIVE belief_chain AS (
  SELECT * FROM nodes WHERE id = ?
  UNION ALL
  SELECT n.* FROM nodes n
  JOIN edges e ON e.source_id = n.id
  JOIN belief_chain bc ON bc.id = e.target_id
  WHERE e.edge_type = 'parent_child'
)
SELECT * FROM belief_chain WHERE type = 'belief';
```

### Find unverified implementations

```sql
SELECT n.* FROM nodes n
WHERE n.type = 'implementation'
AND NOT EXISTS (
  SELECT 1 FROM edges e
  WHERE e.target_id = n.id
  AND e.edge_type = 'verifies'
);
```

### Find nodes linked to coherence rules

SQLite cannot evaluate arbitrary coherence predicates by itself. Use this query to list nodes and linked coherence rule nodes, then run project-local predicate checks in code or manual evidence.

```sql
SELECT n.*, c.data->>'rule_id' as rule_id, c.data as rule_data
FROM nodes n
JOIN edges e ON e.source_id = n.id
JOIN nodes c ON c.id = e.target_id
WHERE e.edge_type = 'constrains'
AND c.type = 'verification';
```
