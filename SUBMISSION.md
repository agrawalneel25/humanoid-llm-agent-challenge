# Submission Notes

**Repository:** https://github.com/agrawalneel25/humanoid-llm-agent-challenge

## What I built

An LLM agent harness for a small 2D grid world. The world contains walls, a locked door, a key, and a red cube. The agent receives a structured JSON observation of its local surroundings, returns one typed action per step, and is judged on whether it actually reaches the goal cell with the key in inventory and the door open.

The focus is the harness, not the world. The env is the source of truth: it validates every action, rejects invalid ones with a readable message, and checks success from world state rather than the model's claim.

On top of the default hand-built world, the repo also includes a procedural room generator, a BFS solver, and a small benchmark that runs the scripted agent across 20 random rooms.

## How to run

No third-party dependencies. Scripted baseline:

```
python -m src.run_demo --agent scripted --render
```

Procedurally generated room:

```
python -m src.run_demo --agent scripted --seed 7 --render
```

LLM agent (needs `OPENAI_API_KEY`):

```
set OPENAI_API_KEY=...
python -m src.run_demo --agent openai --model gpt-4o-mini
```

Procedural benchmark across 20 seeds:

```
python -m src.benchmark --num-seeds 20
```

Tests:

```
python -m unittest discover -s tests
```

## What I measured

[results/scripted_run.log](results/scripted_run.log) is the full rendered trajectory for the default world: 9 steps, 0 invalid actions, success.

[results/benchmark.md](results/benchmark.md) is the procedural batch: 20 random 9x7 rooms, **20/20 success, mean 13.2 steps, 0 invalid actions**. The BFS solver drives the scripted agent for each layout.

## Repository layout

| path | purpose |
| --- | --- |
| `src/environment.py` | grid env, observation, action validation, success check, ASCII render |
| `src/schemas.py` | `AgentAction` dataclass (one action per step) |
| `src/worlds.py` | `make_default_world`, procedural `generate_room(seed)` |
| `src/solver.py` | BFS over (position, has_key, door_open) returning an env-compatible plan |
| `src/agent.py` | `ScriptedAgent` (BFS-driven baseline) and `OpenAIAgent` (Responses API via urllib) |
| `src/run_demo.py` | CLI: pick agent, optional seed for procedural world, optional `--render` |
| `src/benchmark.py` | CLI: run scripted agent over N seeds, emit a markdown table |
| `tests/` | 15 tests covering env, solver, procedural generator |
| `results/` | scripted trajectory and benchmark table |

## Design choices

Full notes are in the README under "Design notes". Headline summary:

- **Local sensing only.** The 4-neighbourhood plus the cell under the agent. Full map made the model pattern-match instead of navigate.
- **Agent-relative actions.** Six verbs with directions relative to facing. World-relative would be easier but masks whether the model is reasoning about state.
- **Env is the source of truth.** Invalid actions return `ok=False` with a message; success is checked from world state, never from a `finish` claim.
- **BFS baseline.** The scripted agent uses BFS over `(position, has_key, door_open)` to produce a shortest plan; same action contract as the LLM agent, so the comparison is honest.
- **No SDK dependency.** The OpenAI integration uses stdlib `urllib` against the Responses API.

## Limitations

- Procedural rooms are single-divider, single-door. Richer layouts would need a different generator.
- The LLM agent has been exercised end-to-end but not batch-evaluated across models or seeds.
- The `note` field is debug-only; the model has no memory channel beyond `last_action`.
- BFS planning ignores `turn`, so the scripted agent never turns.
