# LLM Agent in a Virtual Robotics Lab

This project drops an LLM-controlled agent into a small virtual robotics lab. The world is a deterministic 2D grid containing walls, a locked door, a key and a red calibration cube. The agent receives structured observations, picks one action per step from a fixed action space, and is graded on whether it actually finishes a concrete task.

Example task:

> Find the key, open the locked lab door, reach the red cube, and finish.

The focus is the harness — the interface between the model and an environment it can act in — not the world itself.

## Observation format

Each step the agent receives compact JSON:

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

The model sees only its local 4-neighbourhood plus the cell underneath it, its inventory, and the env's verdict on whatever it tried last.

## Action space

The model must produce one JSON action per step:

```json
{"action": "move", "direction": "forward"}
```

Supported actions:

- `move`: `forward`, `backward`, `left`, `right`
- `turn`: `left`, `right`
- `look`
- `pick_up`
- `open`: `forward`, `backward`, `left`, `right`
- `finish`

Invalid actions are rejected and logged; the agent gets the rejection back in the next `last_action`.

## Run

Scripted deterministic demo, no API key needed:

```bash
python -m src.run_demo --agent scripted
```

OpenAI-backed LLM demo:

```bash
pip install -r requirements.txt
set OPENAI_API_KEY=your_key_here
python -m src.run_demo --agent openai --model gpt-4o-mini
```

PowerShell:

```powershell
pip install -r requirements.txt
$env:OPENAI_API_KEY="your_key_here"
python -m src.run_demo --agent openai --model gpt-4o-mini
```

## Example output

```text
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

A copy is saved in [examples/successful_run.log](examples/successful_run.log).

## Tests

```bash
python -m unittest discover -s tests
```

## Design notes

### Observation representation

The observation is JSON, not free text. The model gets `step`, `position`, `facing`, `inventory`, `goal`, `visible_cells` and `last_action`. Two non-obvious choices:

- **Local sensing only.** `visible_cells` is just the four neighbours plus the cell under the agent. A real robot doesn't get an oracle view of the room, and giving the LLM the full grid encouraged it to pattern-match on the map instead of acting on what it could currently see. Local sensing forces it to move and probe.
- **The goal is in every observation.** It costs a few tokens, but means a step taken with a truncated history still has its objective. Useful when iterating on long runs.
- **`last_action` echoes the env's verdict.** The model finds out within one step whether what it just tried was rejected, and why. This is most of how it self-corrects.

### Action space

Six verbs and a single optional `direction` (forward / backward / left / right). Two deliberate choices:

- **Directions are agent-relative, not world-relative.** The model has to combine `facing` with the direction it wants. That's closer to how a robot actually controls itself, and it surfaces whether the model is genuinely reasoning about state vs. guessing.
- **Invalid combinations don't crash.** `move` with no direction, `open` at a wall, `pick_up` on empty floor — all come back as `ok=False` with a human-readable message. The env stays the source of truth and the model gets a chance to react.

### Harness boundaries

- The model never mutates state directly. It returns one `AgentAction`, the env validates and applies it, and only then does the next observation get rendered.
- Success is checked from world state — `position == cube AND key in inventory AND door open` — never from the model's `finish` claim. The agent has to actually be there.
- The OpenAI integration uses structured outputs: the API is told the schema (pydantic `AgentAction`) and returns a typed object. No regex repair, no JSON-parsing fallbacks.

### What worked, what didn't

- **Worked:** schema-constrained sampling. Once the model couldn't emit free-form prose, the "agent picked an invalid action" failure mode disappeared.
- **Worked:** echoing `last_action` back to the model. Cheaper than any kind of planning scaffolding and accounted for most of the recovery behaviour I saw.
- **Didn't work:** asking the model to maintain its own map of the room across turns. It drifted within a few steps. Replaced with local sensing and a clear goal — the env carries the state, the model just decides the next move.
- **Open:** there's no scratchpad / forced chain-of-thought. The `note` field on `AgentAction` is for trajectory debugging, not internal reasoning. On larger maps an explicit memory channel (e.g. agent-maintained notes the env passes back) would probably matter.

### Why this shape of project

Robotics software needs clean boundaries between perception, planning and actuation. This environment mirrors that discipline at toy scale: the LLM can reason, but it can only change the world through validated actions; success is measured from state, not narration; every step is logged and replayable.
