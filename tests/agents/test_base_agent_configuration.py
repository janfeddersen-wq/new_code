from unittest.mock import MagicMock, patch

import pytest

from newcode.agents.agent_code_agent import CodeAgent


class TestBaseAgentConfiguration:
    @pytest.fixture
    def agent(self):
        return CodeAgent()

    def test_load_agent_rules_no_file(self, agent):
        # Test when no AGENTS.md exists
        with patch("pathlib.Path.exists", return_value=False):
            result = agent.load_agent_rules()
            assert result is None

    def test_load_agent_rules_with_file(self, agent, tmp_path, monkeypatch):
        # Test with actual temp file in project directory
        rules_file = tmp_path / "AGENTS.md"
        rules_file.write_text("Test rules")

        # Clear any cached rules
        agent._agent_rules = None

        # Change to temp directory so Path("AGENTS.md") finds our file
        monkeypatch.chdir(tmp_path)

        # Mock CONFIG_DIR to a non-existent location so global rules aren't found
        with patch("newcode.config.CONFIG_DIR", str(tmp_path / "nonexistent")):
            result = agent.load_agent_rules()
            assert result == "Test rules"

    def test_load_agent_rules_caching(self, agent):
        # Test caching functionality
        agent._agent_rules = "Cached rules"
        result = agent.load_agent_rules()
        assert result == "Cached rules"

    def test_load_mcp_servers_disabled(self, agent):
        # Test when MCP is disabled
        with patch("newcode.config.get_value", return_value="true"):
            result = agent.load_mcp_servers()
            assert isinstance(result, list)
            assert result == []

    def test_load_mcp_servers_true_variants(self, agent):
        # Test various true values for disabled config
        for true_val in ["1", "true", "yes", "on"]:
            with patch("newcode.config.get_value", return_value=true_val):
                result = agent.load_mcp_servers()
                assert isinstance(result, list)

    def test_load_mcp_servers_empty_config(self, agent):
        # Test with empty config and no existing servers
        with (
            patch("newcode.config.get_value", return_value="false"),
            patch("newcode.config.load_mcp_server_configs", return_value={}),
        ):
            mock_manager = MagicMock()
            mock_manager.list_servers.return_value = []
            mock_manager.get_servers_for_agent.return_value = []
            with patch("newcode.mcp_.get_mcp_manager", return_value=mock_manager):
                result = agent.load_mcp_servers()
                assert isinstance(result, list)

    def test_load_mcp_servers_with_existing_servers(self, agent):
        # Test with existing servers when config is empty
        with (
            patch("newcode.config.get_value", return_value="false"),
            patch("newcode.config.load_mcp_server_configs", return_value={}),
        ):
            mock_manager = MagicMock()
            mock_server = MagicMock()
            mock_manager.list_servers.return_value = [mock_server]
            mock_manager.get_servers_for_agent.return_value = [mock_server]
            with patch("newcode.mcp_.get_mcp_manager", return_value=mock_manager):
                result = agent.load_mcp_servers()
                assert isinstance(result, list)

    def test_reload_mcp_servers(self, agent):
        # Test reload functionality
        mock_manager = MagicMock()
        mock_manager.get_servers_for_agent.return_value = [MagicMock()]
        with (
            patch("newcode.mcp_.get_mcp_manager", return_value=mock_manager),
            patch.object(agent, "load_mcp_servers"),
        ):
            result = agent.reload_mcp_servers()
            assert isinstance(result, list)

    def test_load_model_with_fallback_success(self, agent):
        # Test successful model load
        test_model = MagicMock()
        models_config = {"gpt-4": {"provider": "openai"}}

        with patch(
            "newcode.model_factory.ModelFactory.get_model", return_value=test_model
        ):
            model, model_name = agent._load_model_with_fallback(
                "gpt-4", models_config, "test_group"
            )
            assert model == test_model
            assert model_name == "gpt-4"

    def test_load_model_with_fallback_success_different_model(self, agent):
        # Test successful model load with fallback
        test_model = MagicMock()
        models_config = {
            "gpt-4": {"provider": "openai"},
            "claude-3": {"provider": "anthropic"},
        }

        with (
            patch("newcode.model_factory.ModelFactory.get_model") as mock_get_model,
            patch(
                "newcode.agents.base_agent.get_global_model_name",
                return_value="gpt-4",
            ),
        ):
            # First call fails, second succeeds
            mock_get_model.side_effect = [ValueError("Not found"), test_model]

            model, model_name = agent._load_model_with_fallback(
                "nonexistent", models_config, "test_group"
            )

            assert model == test_model
            # The fallback should be one of the available models in the config
            assert model_name in list(models_config.keys())

    def test_load_model_with_fallback_empty_config(self, agent):
        # Test with empty models config
        with patch(
            "newcode.model_factory.ModelFactory.get_model",
            side_effect=ValueError("No models"),
        ):
            models_config = {}

            with pytest.raises(ValueError):
                agent._load_model_with_fallback(
                    "nonexistent", models_config, "test_group"
                )

    def test_load_mcp_servers_with_config(self, agent):
        # Test with actual server configs
        test_configs = {
            "test_server": {
                "id": "test-id",
                "type": "sse",
                "enabled": True,
                "config": {"url": "http://test"},
            }
        }
        mock_manager = MagicMock()
        mock_manager.get_server_by_name.return_value = None
        mock_manager.get_servers_for_agent.return_value = []

        with (
            patch("newcode.config.get_value", return_value="false"),
            patch("newcode.config.load_mcp_server_configs", return_value=test_configs),
            patch("newcode.mcp_.get_mcp_manager", return_value=mock_manager),
        ):
            result = agent.load_mcp_servers()
            # Just verify it returns a list and doesn't crash
            assert isinstance(result, list)

    def test_load_mcp_servers_basic(self, agent):
        # Basic test that method returns a list
        with (
            patch("newcode.config.get_value", return_value="false"),
            patch("newcode.config.load_mcp_server_configs", return_value={}),
        ):
            mock_manager = MagicMock()
            mock_manager.list_servers.return_value = []
            mock_manager.get_servers_for_agent.return_value = []
            with patch("newcode.mcp_.get_mcp_manager", return_value=mock_manager):
                result = agent.load_mcp_servers()
                assert isinstance(result, list)


class TestCodePuppyPrompt:
    """Test that the Code-Puppy system prompt contains expected sections."""

    @pytest.fixture
    def agent(self):
        return CodeAgent()

    def test_prompt_contains_core_sections(self, agent):
        """Core prompt sections must be present."""
        prompt = agent.get_system_prompt()
        for expected in [
            "edit_file",
            "run_shell_command",
            "list_files",
            "invoke_agent",
            "ask_user_question",
            "production-ready, maintainable",
        ]:
            assert expected in prompt, f"Missing in prompt: {expected}"

    def test_prompt_does_not_mention_share_your_reasoning(self, agent):
        """share_your_reasoning tool has been removed."""
        prompt = agent.get_system_prompt()
        assert "share_your_reasoning" not in prompt
