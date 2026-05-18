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


if __name__ == "__main__":
    unittest.main()
