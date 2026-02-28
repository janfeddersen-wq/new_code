"""Additional coverage tests for cli_runner.py - uncovered branches.

Focuses on: run_prompt_with_attachments, execute_single_prompt, main_entry,
and interactive_mode branches.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRunPromptWithAttachments:
    """Test run_prompt_with_attachments function."""

    @pytest.mark.anyio
    async def test_empty_prompt_returns_none(self):
        from newcode.cli_runner import run_prompt_with_attachments

        # A prompt that becomes empty after attachment parsing
        mock_agent = MagicMock()
        with (
            patch("newcode.cli_runner.parse_prompt_attachments") as mock_parse,
            patch("newcode.cli_runner.get_clipboard_manager") as mock_clip,
        ):
            mock_parse.return_value = MagicMock(
                prompt="",
                warnings=[],
                attachments=[],
                link_attachments=[],
            )
            clip_mgr = MagicMock()
            clip_mgr.get_pending_images.return_value = []
            clip_mgr.get_pending_count.return_value = 0
            mock_clip.return_value = clip_mgr

            result, task = await run_prompt_with_attachments(mock_agent, "")
            assert result is None
            assert task is None

    @pytest.mark.anyio
    async def test_with_attachments_and_spinner(self):
        from newcode.cli_runner import run_prompt_with_attachments

        mock_agent = MagicMock()
        mock_result = MagicMock()
        mock_agent.run_with_mcp = AsyncMock(return_value=mock_result)

        mock_attachment = MagicMock()
        mock_attachment.content = b"image-data"
        mock_link = MagicMock()
        mock_link.url_part = "https://example.com"

        with (
            patch("newcode.cli_runner.parse_prompt_attachments") as mock_parse,
            patch("newcode.cli_runner.get_clipboard_manager") as mock_clip,
            patch("newcode.agents.event_stream_handler.set_streaming_console"),
            patch("newcode.messaging.spinner.ConsoleSpinner") as mock_spinner,
        ):
            mock_parse.return_value = MagicMock(
                prompt="do stuff",
                warnings=["warn1"],
                attachments=[mock_attachment],
                link_attachments=[mock_link],
            )
            clip_mgr = MagicMock()
            clip_mgr.get_pending_images.return_value = [b"clip-img"]
            clip_mgr.get_pending_count.return_value = 1
            mock_clip.return_value = clip_mgr

            mock_spinner.return_value.__enter__ = MagicMock()
            mock_spinner.return_value.__exit__ = MagicMock(return_value=False)

            console = MagicMock()
            result, task = await run_prompt_with_attachments(
                mock_agent, "do stuff", spinner_console=console, use_spinner=True
            )
            assert result is mock_result

    @pytest.mark.anyio
    async def test_cancelled_with_spinner(self):
        from newcode.cli_runner import run_prompt_with_attachments

        mock_agent = MagicMock()
        mock_agent.run_with_mcp = AsyncMock(side_effect=asyncio.CancelledError)

        with (
            patch("newcode.cli_runner.parse_prompt_attachments") as mock_parse,
            patch("newcode.cli_runner.get_clipboard_manager") as mock_clip,
            patch("newcode.agents.event_stream_handler.set_streaming_console"),
            patch("newcode.messaging.spinner.ConsoleSpinner") as mock_spinner,
        ):
            mock_parse.return_value = MagicMock(
                prompt="do stuff",
                warnings=[],
                attachments=[],
                link_attachments=[],
            )
            clip_mgr = MagicMock()
            clip_mgr.get_pending_images.return_value = []
            clip_mgr.get_pending_count.return_value = 0
            mock_clip.return_value = clip_mgr

            mock_spinner.return_value.__enter__ = MagicMock()
            mock_spinner.return_value.__exit__ = MagicMock(return_value=False)

            console = MagicMock()
            result, task = await run_prompt_with_attachments(
                mock_agent, "do stuff", spinner_console=console, use_spinner=True
            )
            assert result is None

    @pytest.mark.anyio
    async def test_cancelled_without_spinner(self):
        from newcode.cli_runner import run_prompt_with_attachments

        mock_agent = MagicMock()
        mock_agent.run_with_mcp = AsyncMock(side_effect=asyncio.CancelledError)

        with (
            patch("newcode.cli_runner.parse_prompt_attachments") as mock_parse,
            patch("newcode.cli_runner.get_clipboard_manager") as mock_clip,
            patch("newcode.agents.event_stream_handler.set_streaming_console"),
        ):
            mock_parse.return_value = MagicMock(
                prompt="do stuff",
                warnings=[],
                attachments=[],
                link_attachments=[],
            )
            clip_mgr = MagicMock()
            clip_mgr.get_pending_images.return_value = []
            clip_mgr.get_pending_count.return_value = 0
            mock_clip.return_value = clip_mgr

            result, task = await run_prompt_with_attachments(
                mock_agent, "do stuff", use_spinner=False
            )
            assert result is None

    @pytest.mark.anyio
    async def test_clipboard_placeholder_cleaned(self):
        from newcode.cli_runner import run_prompt_with_attachments

        mock_agent = MagicMock()
        mock_result = MagicMock()
        mock_agent.run_with_mcp = AsyncMock(return_value=mock_result)

        with (
            patch("newcode.cli_runner.parse_prompt_attachments") as mock_parse,
            patch("newcode.cli_runner.get_clipboard_manager") as mock_clip,
            patch("newcode.agents.event_stream_handler.set_streaming_console"),
        ):
            mock_parse.return_value = MagicMock(
                prompt="[📋 clipboard image 1] describe this",
                warnings=[],
                attachments=[],
                link_attachments=[],
            )
            clip_mgr = MagicMock()
            clip_mgr.get_pending_images.return_value = [b"img"]
            clip_mgr.get_pending_count.return_value = 1
            mock_clip.return_value = clip_mgr

            result, task = await run_prompt_with_attachments(
                mock_agent, "test", use_spinner=False
            )
            # The cleaned prompt should have placeholder removed
            call_args = mock_agent.run_with_mcp.call_args
            assert "clipboard image" not in call_args[0][0]


class TestExecuteSinglePrompt:
    @pytest.mark.anyio
    async def test_success(self):
        from newcode.cli_runner import execute_single_prompt

        mock_renderer = MagicMock()
        mock_renderer.console = MagicMock()

        mock_result = MagicMock()
        mock_result.output = "done!"

        with (
            patch("newcode.cli_runner.get_current_agent"),
            patch(
                "newcode.cli_runner.run_prompt_with_attachments",
                new_callable=AsyncMock,
            ) as mock_run,
            patch("newcode.cli_runner.emit_info"),
        ):
            mock_run.return_value = (mock_result, MagicMock())
            await execute_single_prompt("hello", mock_renderer)

    @pytest.mark.anyio
    async def test_none_response(self):
        from newcode.cli_runner import execute_single_prompt

        mock_renderer = MagicMock()
        mock_renderer.console = MagicMock()

        with (
            patch("newcode.cli_runner.get_current_agent"),
            patch(
                "newcode.cli_runner.run_prompt_with_attachments",
                new_callable=AsyncMock,
            ) as mock_run,
            patch("newcode.cli_runner.emit_info"),
        ):
            mock_run.return_value = None
            await execute_single_prompt("hello", mock_renderer)

    @pytest.mark.anyio
    async def test_cancelled(self):
        from newcode.cli_runner import execute_single_prompt

        mock_renderer = MagicMock()
        mock_renderer.console = MagicMock()

        with (
            patch("newcode.cli_runner.get_current_agent"),
            patch(
                "newcode.cli_runner.run_prompt_with_attachments",
                new_callable=AsyncMock,
                side_effect=asyncio.CancelledError,
            ),
            patch("newcode.cli_runner.emit_info"),
        ):
            await execute_single_prompt("hello", mock_renderer)

    @pytest.mark.anyio
    async def test_exception(self):
        from newcode.cli_runner import execute_single_prompt

        mock_renderer = MagicMock()
        mock_renderer.console = MagicMock()

        with (
            patch("newcode.cli_runner.get_current_agent"),
            patch(
                "newcode.cli_runner.run_prompt_with_attachments",
                new_callable=AsyncMock,
                side_effect=RuntimeError("boom"),
            ),
            patch("newcode.cli_runner.emit_info"),
        ):
            await execute_single_prompt("hello", mock_renderer)


class TestMainEntry:
    @patch("asyncio.run")
    def test_normal_exit(self, mock_run):
        from newcode.cli_runner import main_entry

        mock_run.return_value = None
        with patch("newcode.cli_runner.reset_unix_terminal"):
            result = main_entry()
        assert result is None

    @patch("asyncio.run", side_effect=KeyboardInterrupt)
    def test_keyboard_interrupt(self, mock_run):
        from newcode.cli_runner import main_entry

        with (
            patch("newcode.cli_runner.reset_unix_terminal"),
            patch("newcode.cli_runner.get_use_dbos", return_value=False),
        ):
            result = main_entry()
        assert result == 0

    @patch("asyncio.run", side_effect=KeyboardInterrupt)
    def test_keyboard_interrupt_with_dbos(self, mock_run):
        from newcode.cli_runner import main_entry

        with (
            patch("newcode.cli_runner.reset_unix_terminal"),
            patch("newcode.cli_runner.get_use_dbos", return_value=True),
            patch("newcode.cli_runner.DBOS") as mock_dbos,
        ):
            result = main_entry()
        assert result == 0
        mock_dbos.destroy.assert_called_once()
