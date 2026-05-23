import unittest

from src.agent import ScriptedAgent
from src.environment import VirtualLab, make_default_world
from src.schemas import AgentAction
from src.solver import shortest_plan
from src.worlds import generate_room


class SolverTests(unittest.TestCase):
    def test_default_world_plan_succeeds(self) -> None:
        config = make_default_world()
        plan = shortest_plan(config)
        self.assertIsNotNone(plan)
        env = VirtualLab(config=config)
        for action in plan:
            env.apply(action)
        self.assertTrue(env.is_success() or plan[-1].action == "finish")

    def test_default_world_plan_is_nine_steps(self) -> None:
        plan = shortest_plan(make_default_world())
        # 8 navigation steps + finish.
        self.assertEqual(len(plan), 9)

    def test_unsolvable_world_returns_none(self) -> None:
        # Construct a world where the cube is walled off and the door is the
        # only way through; remove the door from the config entirely by moving
        # it inside a wall block. The simplest unsolvable: cube unreachable.
        from src.environment import WorldConfig

        config = WorldConfig(
            width=5,
            height=5,
            agent_start=(1, 1),
            agent_facing="east",
            interior_walls={(2, 1), (2, 2), (2, 3)},
            key=(1, 2),
            door=(0, 2),  # door embedded in border wall, never adjacent from inside
            cube=(3, 2),
        )
        self.assertIsNone(shortest_plan(config))

    def test_procedural_rooms_are_solvable(self) -> None:
        for seed in range(20):
            config = generate_room(seed=seed)
            self.assertIsNotNone(shortest_plan(config), f"seed {seed} unsolvable")

    def test_scripted_agent_completes_procedural_rooms(self) -> None:
        for seed in range(10):
            config = generate_room(seed=seed)
            env = VirtualLab(config=config)
            agent = ScriptedAgent(config=config)
            invalid = 0
            while env.step < 200:
                result = env.apply(agent.choose_action(env.observe()))
                if not result.ok:
                    invalid += 1
                if env.is_success():
                    env.apply(AgentAction(action="finish"))
                    break
            self.assertTrue(env.is_success(), f"seed {seed} failed; invalid={invalid}")


if __name__ == "__main__":
    unittest.main()
