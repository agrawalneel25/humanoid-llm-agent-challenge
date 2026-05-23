import unittest

from src.environment import VirtualLab
from src.schemas import AgentAction


class EnvironmentTests(unittest.TestCase):
    def test_scripted_path_reaches_success(self) -> None:
        env = VirtualLab()
        actions = [
            AgentAction(action="move", direction="right"),
            AgentAction(action="pick_up"),
            AgentAction(action="move", direction="left"),
            AgentAction(action="move", direction="forward"),
            AgentAction(action="move", direction="forward"),
            AgentAction(action="open", direction="forward"),
            AgentAction(action="move", direction="forward"),
            AgentAction(action="move", direction="forward"),
        ]
        for action in actions:
            result = env.apply(action)
            self.assertTrue(result.ok, result.message)
        self.assertTrue(env.is_success())
        result = env.apply(AgentAction(action="finish"))
        self.assertTrue(result.ok)

    def test_cannot_open_locked_door_without_key(self) -> None:
        env = VirtualLab()
        env.apply(AgentAction(action="move", direction="forward"))
        env.apply(AgentAction(action="move", direction="forward"))
        result = env.apply(AgentAction(action="open", direction="forward"))
        self.assertFalse(result.ok)
        self.assertIn("key is missing", result.message)

    def test_finish_before_success_returns_false(self) -> None:
        env = VirtualLab()
        result = env.apply(AgentAction(action="finish"))
        self.assertFalse(result.ok)
        self.assertEqual(result.message, "goal not complete")

    def test_move_into_border_wall_is_rejected(self) -> None:
        env = VirtualLab()
        # Agent at (1, 1) facing east; moving backward targets (0, 1), a border wall.
        result = env.apply(AgentAction(action="move", direction="backward"))
        self.assertFalse(result.ok)
        self.assertIn("wall", result.message)
        self.assertEqual(env.position, (1, 1))

    def test_pick_up_off_key_is_rejected(self) -> None:
        env = VirtualLab()
        result = env.apply(AgentAction(action="pick_up"))
        self.assertFalse(result.ok)
        self.assertIn("nothing", result.message)
        self.assertEqual(env.inventory, [])

    def test_turn_cycles_through_all_facings(self) -> None:
        env = VirtualLab()
        self.assertEqual(env.facing, "east")
        for expected in ["south", "west", "north", "east"]:
            env.apply(AgentAction(action="turn", direction="right"))
            self.assertEqual(env.facing, expected)

    def test_invalid_action_lets_env_recover(self) -> None:
        env = VirtualLab()
        bad = env.apply(AgentAction(action="open", direction="forward"))
        self.assertFalse(bad.ok)
        # Env state should be intact; the next valid action proceeds normally.
        good = env.apply(AgentAction(action="move", direction="right"))
        self.assertTrue(good.ok)
        self.assertEqual(env.position, (1, 2))

    def test_observation_is_local_only(self) -> None:
        env = VirtualLab()
        obs = env.observe()
        relatives = {tuple(c["relative"]) for c in obs["visible_cells"]}
        self.assertEqual(relatives, {(0, -1), (1, 0), (0, 1), (-1, 0), (0, 0)})

    def test_render_shows_walls_and_landmarks(self) -> None:
        env = VirtualLab()
        lines = env.render().split("\n")
        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[0], "#######")
        self.assertEqual(lines[4], "#######")
        self.assertIn(">", lines[1])
        self.assertIn("D", lines[1])
        self.assertIn("R", lines[1])
        self.assertIn("K", lines[2])

    def test_open_door_is_passable_and_persistent(self) -> None:
        env = VirtualLab()
        # Walk to key, pick up, walk back to (3, 1), open door, walk through.
        for action in [
            AgentAction(action="move", direction="right"),
            AgentAction(action="pick_up"),
            AgentAction(action="move", direction="left"),
            AgentAction(action="move", direction="forward"),
            AgentAction(action="move", direction="forward"),
            AgentAction(action="open", direction="forward"),
        ]:
            self.assertTrue(env.apply(action).ok)
        # Door at (4, 1) should now be open in the rendered grid.
        self.assertIn("/", env.render())
        # And passable.
        self.assertTrue(env.apply(AgentAction(action="move", direction="forward")).ok)
        self.assertEqual(env.position, (4, 1))


if __name__ == "__main__":
    unittest.main()
