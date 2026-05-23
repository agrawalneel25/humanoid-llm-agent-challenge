# LLM Agent in a Virtual Robotics Lab

A small 2D grid world: walls, a locked door, a key, and a red cube. An LLM picks one action per step, the env validates it, and the agent has to actually reach the cube to win.

The interesting bit is the harness, not the world. The world is intentionally tiny so the model has nowhere to hide.

```
#######
#>..DR#
#K##..#
#.....#
#######
```

`>` is the agent (east-facing), `K` the key, `D` the locked door, `R` the red cube, `#` a wall.

Goal:

> Find the key, open the locked lab door, reach the red cube, and finish.

## Observation

Each step the model sees:

```json
{
  "step": 3,
  "position": [1, 2],
  "facing": "south",
  "inventory": ["key"],
  "goal": "Find the key, open the locked lab door, reach the red cube, and finish.",
  "visible_cells": [
    {"relative": [0, 1], "position": [1, 3], "type": "empty"},
    {"relative": [1, 0], "position": [2, 2], "type": "wall"}
  ],
  "last_action": {"ok": true, "message": "picked up key"}
}
```

`visible_cells` is the 4-neighbourhood plus the cell under the agent. There is no oracle map.

## Actions

One action per step:

```json
{"action": "move", "direction": "forward"}
```

- `move`: forward / backward / left / right
- `turn`: left / right
- `look`
- `pick_up`
- `open`: forward / backward / left / right
- `finish`

Invalid actions come back with `ok=False` and a message; the model sees the rejection in the next step's `last_action`.

## Run

No third-party dependencies. Scripted demo (deterministic, BFS-planned):

```
python -m src.run_demo --agent scripted
```

Render the grid at each step:

```
python -m src.run_demo --agent scripted --render
```

Procedurally generated room (different layout per seed):

```
python -m src.run_demo --agent scripted --seed 7 --render
```

LLM agent (needs `OPENAI_API_KEY`; the agent talks to the Responses API via stdlib `urllib`, no SDK install required):

```
set OPENAI_API_KEY=...
python -m src.run_demo --agent openai --model gpt-4o-mini
```

PowerShell: `$env:OPENAI_API_KEY="..."` instead of `set`.

## Default-world trajectory

```
01 action=move right ok=True msg=moved to (1, 2)
02 action=pick_up ok=True msg=picked up key
03 action=move left ok=True msg=moved to (1, 1)
04 action=move forward ok=True msg=moved to (2, 1)
05 action=move forward ok=True msg=moved to (3, 1)
06 action=open forward ok=True msg=opened door at (4, 1)
07 action=move forward ok=True msg=moved to (4, 1)
08 action=move forward ok=True msg=moved to (5, 1)
09 action=finish ok=True msg=success
```

Full rendered trajectory: [results/scripted_run.log](results/scripted_run.log).

## Procedural benchmark

A small procedural generator drops a single dividing wall with one door, picks key / cube / agent positions on opposite sides, and rejects layouts the BFS solver cannot solve. The scripted agent then runs end to end.

```
python -m src.benchmark --num-seeds 20
```

Results across 20 seeds (9x7 rooms): **20/20 success, mean 13.2 steps, 0 invalid actions**. Full table: [results/benchmark.md](results/benchmark.md).

## Tests

```
python -m unittest discover -s tests
```

15 tests covering env mechanics, action validation, solver correctness on the default world, solver correctness over procedural seeds, and end-to-end scripted execution on procedural rooms.

## Design notes

**Observations.** Local 4-neighbourhood plus the cell under the agent, rather than the full map. The world is small enough that I could've just handed over the whole grid, but doing that lets the model pattern-match the layout instead of actually navigating, which defeats the point of the harness. Local sensing also matches how a real robot perceives. The cost is that anything bigger than this would need some form of memory; the natural extension is an agent-maintained notes channel carried through `last_action`.

The `last_action` echo does more work than it looks. It is the only feedback channel for "you tried something, here is what happened". Without it the model has no way to know an action was rejected and will just keep emitting the same invalid move.

**Actions.** Six verbs, all relative to facing. World-relative directions would be easier for the model, but they are not what a robot actually does, and I wanted the harness to surface whether the model is reasoning about state. Invalid actions do not crash. They get rejected with `ok=False` and a human-readable message, which keeps the loop intact when the model hallucinates a direction.

**Harness boundaries.** Only the env mutates state. The model returns an `AgentAction` and never touches the world directly. Success is checked from world state (`position == cube AND key in inventory AND door open`), not from the model claiming `finish`. The OpenAI integration is a thin wrapper around the Responses API via stdlib `urllib`: no extra installs, no SDK to keep in sync, and JSON extraction includes a regex fallback for the occasional time the model wraps the reply in prose.

**Baseline vs. world.** The scripted agent runs a BFS plan against the same env contract the LLM sees. That keeps the comparison honest: the agent and the baseline are evaluated on the same action language, the same observation format, and the same success check. The procedural benchmark stress-tests that this contract holds across different layouts.

**What I didn't do.** No chain-of-thought scaffolding, no planning step on the LLM side. The `note` field on the action is for trajectory debugging only, not internal reasoning. For larger or sparser maps that would matter; for this one, single-shot decisions are fine.

## Limitations

- The procedural generator places exactly one dividing wall with one door. Multi-room mazes would need a different generator and a richer key/door inventory.
- The LLM agent has been exercised end-to-end against the env contract but I have not run a batch comparison across models or seeds.
- The `note` field is debug-only. The model has no separate memory channel, so anything that needs the agent to remember more than the last action would need extra observation fields.
- BFS planning ignores the cost of `turn`. The plan emits agent-relative moves computed from the initial facing, so the agent never turns in the default scripted runs. If `turn` were costly this would no longer be optimal.
