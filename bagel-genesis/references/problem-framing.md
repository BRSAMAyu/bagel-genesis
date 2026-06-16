# Problem Framing Protocol

Use after deep alignment and before Build. Also use after repeated lateral cycles or when current progress is technically correct but not valuable.

Top experts do not blindly solve the stated problem. They ask whether it is the right problem.

```yaml
problem_framing:
  user_stated_problem: ""
  inferred_real_problem: ""
  possible_reframings:
    - framing: ""
      why_better: ""
      risk: ""
      cheap_probe: ""
  chosen_framing: ""
  rejected_framings:
    - framing: ""
      why_rejected: ""
```

Rules:

- For `deep_alignment` and `full_expert_run`, include at least three possible reframings.
- Do not enter Build until `chosen_framing` exists.
- If the chosen framing changes product/research identity, route to Constitutional Court and user hard-stop policy.
