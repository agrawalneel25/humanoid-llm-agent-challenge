from __future__ import annotations

import argparse

from .agent import OpenAIAgent, ScriptedAgent
from .environment import VirtualLab


def run(agent_name: str, model: str, max_steps: int) -> int:
    env = VirtualLab()
    agent = OpenAIAgent(model) if agent_name == "openai" else ScriptedAgent()
    for _ in range(max_steps):
        obs = env.observe()
        action = agent.choose_action(obs)
        result = env.apply(action)
        direction = f" {action.direction}" if action.direction else ""
        print(
            f"{env.step:02d} action={action.action}{direction} "
            f"ok={result.ok} msg={result.message}"
        )
        if action.action == "finish":
            return 0 if result.ok else 1
        if env.is_success():
            finish = agent.choose_action(env.observe())
            if finish.action != "finish":
                finish.action = "finish"
            result = env.apply(finish)
            print(f"{env.step:02d} action=finish ok={result.ok} msg={result.message}")
            return 0 if result.ok else 1
    print("step limit reached")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", choices=["scripted", "openai"], default="scripted")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--max-steps", type=int, default=30)
    args = parser.parse_args()
    raise SystemExit(run(args.agent, args.model, args.max_steps))


if __name__ == "__main__":
    main()
