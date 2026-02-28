"""Tests for scheduler CLI commands."""

from unittest.mock import patch

from newcode.scheduler.cli import (
    handle_scheduler_list,
    handle_scheduler_status,
)


class TestSchedulerCLI:
    """Tests for CLI command handlers."""

    @patch("newcode.scheduler.daemon.get_daemon_pid")
    @patch("newcode.scheduler.config.load_tasks")
    def test_status_daemon_running(self, mock_load, mock_pid):
        """Test status when daemon is running."""
        mock_pid.return_value = 12345
        mock_load.return_value = []

        result = handle_scheduler_status()

        assert result is True
        mock_pid.assert_called_once()

    @patch("newcode.scheduler.daemon.get_daemon_pid")
    @patch("newcode.scheduler.config.load_tasks")
    def test_status_daemon_stopped(self, mock_load, mock_pid):
        """Test status when daemon is stopped."""
        mock_pid.return_value = None
        mock_load.return_value = []

        result = handle_scheduler_status()

        assert result is True

    @patch("newcode.scheduler.config.load_tasks")
    def test_list_empty(self, mock_load):
        """Test listing when no tasks exist."""
        mock_load.return_value = []

        result = handle_scheduler_list()

        assert result is True

    @patch("newcode.scheduler.config.load_tasks")
    def test_list_with_tasks(self, mock_load):
        """Test listing tasks."""
        from newcode.scheduler.config import ScheduledTask

        mock_load.return_value = [
            ScheduledTask(name="Task 1", prompt="Prompt 1"),
            ScheduledTask(name="Task 2", prompt="Prompt 2"),
        ]

        result = handle_scheduler_list()

        assert result is True
