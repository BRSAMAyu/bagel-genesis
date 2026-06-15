# Alignment Dashboard HTML

Use when BAGEL should show the user alignment state, project reality, run strategy, and progress in a more visual way than Markdown.

This is an auxiliary briefing artifact. It must not become the source of truth. Generate it from `.bagel/constitution.yaml`, `.bagel/context.yaml`, `.bagel/state.yaml`, `.bagel/ledger.yaml`, and `.bagel/evidence/progress-deltas.yaml`.

## Output

Default path:

```text
.bagel/user_briefing/alignment-dashboard.html
```

The page should be a single self-contained HTML file with inline CSS and JS. Avoid build tools unless the project already uses them.

## Presentation Mode Choice

Ask when the user will actively inspect the briefing:

```yaml
question: "How should BAGEL present the alignment briefing?"
options:
  - label: "Continuous dashboard"
    description: "Recommended: one scrollable high-density view for fast understanding."
  - label: "Section tabs"
    description: "A single page with tabs for Vision, Project Reality, Runtime, Risks, and Progress."
  - label: "Slide-like walkthrough"
    description: "Best for a live review, but not the default for overnight status."
```

Style choice:

```yaml
question: "What visual style should the dashboard use?"
options:
  - label: "Calm operator"
    description: "Dense, precise, low-decoration, good for engineering status."
  - label: "Product studio"
    description: "More visual hierarchy and polish for app/product work."
  - label: "Research lab"
    description: "Evidence-first layout for experiments, benchmarks, and claims."
```

Update frequency:

```yaml
question: "How often should the HTML briefing update?"
options:
  - label: "Every milestone"
    description: "Lower overhead; best default."
  - label: "Every cycle"
    description: "Most current, higher overhead."
  - label: "Final only"
    description: "Use when runtime budget should go almost entirely to artifact work."
```

## Layout Rules

Prefer a continuous dashboard over frequent page-flipping:

- sticky top summary with run status, elapsed time, strategy, next action,
- compact cards for decisions and hard-stops,
- project reality split: protected vs. replaceable,
- progress strip: cycles, agents dispatched, compactions, tests, screenshots, telemetry,
- evidence timeline with links to local artifacts,
- risk and blocked-lane panel,
- morning review checklist for defaults, assumptions, and veto-needed items.

Keep it information-rich but readable. Use restrained animation: initial reveal, subtle progress updates, no distracting slide transitions.

## Content Contract

The dashboard must clearly label:

- user-approved decision,
- system default,
- repo-evidence inference,
- open assumption,
- stale or disputed fact,
- hard-stop boundary,
- isolated lane.

Never hide uncertainty for visual polish. If state files conflict, show `STATE CONFLICT` at the top and link to the conflict report.

## Implementation Guidance

Use a single HTML page:

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>BAGEL Alignment Dashboard</title>
  <style>
    :root {
      --bg: #0f1115;
      --panel: #171a21;
      --text: #f4f1e8;
      --muted: #a8adbb;
      --accent: #63d6b5;
      --warn: #f2b84b;
      --danger: #ef6f6c;
    }
    body { margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: var(--bg); color: var(--text); }
    main { max-width: 1280px; margin: 0 auto; padding: 28px; }
    .topbar { position: sticky; top: 0; z-index: 2; background: color-mix(in srgb, var(--bg) 92%, transparent); backdrop-filter: blur(12px); padding: 16px 0; }
    .grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; }
    .panel { background: var(--panel); border: 1px solid rgba(255,255,255,.08); border-radius: 8px; padding: 18px; }
    .span-4 { grid-column: span 4; } .span-6 { grid-column: span 6; } .span-8 { grid-column: span 8; } .span-12 { grid-column: span 12; }
    @media (max-width: 840px) { .span-4, .span-6, .span-8 { grid-column: span 12; } main { padding: 16px; } }
  </style>
</head>
<body>
  <main>
    <section class="topbar">...</section>
    <section class="grid">...</section>
  </main>
</body>
</html>
```

Use project-specific colors and typography when known, but do not over-design. The point is fast comprehension.

## Verification

Before presenting the dashboard:

1. Open it locally or via browser tooling.
2. Check desktop and mobile widths.
3. Verify text does not overlap or overflow.
4. Verify links to evidence files exist.
5. Ensure no chain-of-thought or raw transcripts are embedded.
