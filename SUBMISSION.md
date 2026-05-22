# Submission Notes

**Repository:** https://github.com/agrawalneel25/humanoid-llm-agent-challenge

## What I built

An LLM agent harness for a small 2D grid world. The world contains walls, a locked door, a key, and a red cube. The agent receives structured JSON observations of its local surroundings, returns one typed action per step, and is judged on whether it actually reaches the goal cell with the key in inventory and the door open.

The focus is the harness, not the world. The env is the source of truth: it validates every action, rejects invalid ones with a readable message, and checks success from world state rather than from the model's claim.

## How to run

Scripted baseline (no API key):

```
python -m src.run_demo --agent scripted
```

LLM agent:

```
pip install -r requirements.txt
set OPENAI_API_KEY=...
python -m src.run_demo --agent openai --model gpt-4o-mini
```

Tests:

```
python -m unittest discover -s tests
```

## What I measured

[results/metrics.md](results/metrics.md) summarises the scripted baseline: 9 steps to success, 0 invalid actions, deterministic. The same loop drives the LLM agent; I did not run a batch comparison across models or seeds.

## What is in the box

| path | purpose |
| --- | --- |
| `src/environment.py` | grid world, observation, action validation, success check |
| `src/schemas.py` | pydantic action schema for structured outputs |
| `src/agent.py` | `ScriptedAgent` (baseline) and `OpenAIAgent` (LLM) |
| `src/run_demo.py` | CLI runner: picks an agent and loops to goal or step limit |
| `tests/test_environment.py` | success path and locked-door failure path |
| `results/scripted_run.log` | full trajectory of the scripted baseline |
| `results/metrics.md` | one-page summary of what the scripted run shows |

## Design choices

Full notes are in the README under "Design notes". One-line summary of the four choices:

- Local 4-neighbourhood observation (not full map), so the model has to navigate rather than read coordinates.
- Six verbs with directions relative to facing, so the harness surfaces state reasoning.
- Structured outputs (pydantic schema), so there is no JSON-parsing fallback path.
- Success checked from world state, not the model claiming `finish`.

## Limitations

- The world is hand-built and tiny. Procedural generation would be the natural next step.
- The LLM agent has been exercised end-to-end but not benchmarked across seeds or models.
- The `note` field on actions is debug-only; the model has no separate memory channel.
- No CI matrix yet across Python versions.
