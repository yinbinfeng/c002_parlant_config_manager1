import unittest
from pathlib import Path

from src.mining_agents.utils.config_loader import ConfigLoader


class TestConfigLoaderDynamicAgentName(unittest.TestCase):
    def test_dynamic_agent_name_should_fallback_to_base_agent_config(self):
        config_dir = (
            Path(__file__).resolve().parents[1]
            / "egs"
            / "v0.1.0_minging_agents"
            / "config"
            / "agents"
        )
        loader = ConfigLoader(str(config_dir))

        cfg = loader.load_agent_config("ProcessAgent_node_000")

        # 动态实例名应回退到 process_agent.yaml，而不是默认空配置
        self.assertEqual(cfg.get("agent_name"), "ProcessAgent")
        self.assertIn("task_prompts", cfg)
        self.assertIn("design_process", cfg.get("task_prompts", {}))


if __name__ == "__main__":
    unittest.main()
