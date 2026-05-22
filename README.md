# LLM Agent in a Virtual Robotics Lab

A small 2D grid world: walls, a locked door, a key, and a red cube. An LLM picks one action per step, the env validates it, and the agent has to actually reach the cube to win.

The interesting bit is the harness, not the world. The world is intentionally tiny so the model has nowhere to hide.

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

`visible_cells` is the 4-neighbourhood plus the cell under the agent — no oracle map.

## Actions

One action per step:

```json
{"action": "move", "direction": "forward"}
```

- `move` — forward / backward / left / right
- `turn` — left / right
- `look`
- `pick_up`
- `open` — forward / backward / left / right
- `finish`

Invalid actions come back with `ok=False` and a message; the model gets the rejection in the next step's `last_action`.

## Run

Scripted demo (no API key):

```
python -m src.run_demo --agent scripted
```

LLM agent:

```
pip install -r requirements.txt
set OPENAI_API_KEY=...
python -m src.run_demo --agent openai --model gpt-4o-mini
```

PowerShell uses `$env:OPENAI_API_KEY="..."` instead of `set`.

## Example trajectory

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

Saved at [examples/successful_run.log](examples/successful_run.log).

## Tests

```
python -m unittest discover -s tests
```

## Design notes

**Observations.** Local 4-neighbourhood plus the cell under the agent, rather than the full map. The world is small enough that I could've just handed over the whole grid, but doing that lets the model pattern-match the layout instead of actually navigating — which defeats the point of the harness. Local sensing also matches how a real robot perceives. The cost is that anything bigger than this would need some kind of memory; the natural extension is an agent-maintained notes channel carried through `last_action`.

The `last_action` echo does more work than it looks. It's the only feedback channel for "you tried something, here's what happened" — without it the model has no way to know an action was rejected and will just keep emitting the same invalid move.

**Actions.** Six verbs, all relative to facing. World-relative directions would be easier for the model, but they're not really what a robot does, and I wanted the harness to surface whether the model is reasoning about state. Invalid actions don't crash — they get rejected with `ok=False` and a human-readable message — which keeps the loop intact when the model hallucinates a direction.

**Harness boundaries.** Only the env mutates state. The model returns a typed `AgentAction` and never touches the world directly. Success is checked from world state (`position == cube AND key in inventory AND door open`), not from the model claiming `finish`. The OpenAI integration uses structured outputs (pydantic schema → typed response), so there's no JSON-parsing fallback path. Free-form text + regex repair is where I'd expect most of a real harness's bugs to live, so the dependency felt worth it.

**What I didn't do.** No chain-of-thought scaffolding, no planning step. The `note` field on the action is for trajectory debugging only, not internal reasoning. For larger or sparser maps that would matter; for this one, single-shot decisions are fine.
