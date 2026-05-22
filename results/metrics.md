# Run metrics

Captured from `python -m src.run_demo --agent scripted` on 2026-05-22.

| metric | value |
| --- | --- |
| world size | 7 x 5 |
| reachable cells | 17 |
| shortest scripted path to goal | 9 steps |
| invalid actions in scripted run | 0 |
| total steps to success in scripted run | 9 |
| final result | `ok=True msg=success` |

Full trajectory: [scripted_run.log](scripted_run.log).

## Notes

The scripted agent is the baseline: it proves the env, the success check, and the action validation all line up. With `--agent openai` the same loop is driven by the model. I have not run a batch comparison across models or seeds; that would be the natural next step.

A useful follow-up metric would be `invalid_action_rate` for the LLM agent across N independent runs at temperature > 0. Lower is better. With structured outputs constrained by the pydantic schema, I would expect this to be near zero. Worth measuring.
