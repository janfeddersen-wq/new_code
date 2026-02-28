"""Full coverage tests for scheduler/cli.py."""

from unittest.mock import patch

from newcode.scheduler.config import ScheduledTask


class TestHandleSchedulerStart:
    def test_already_running(self):
        from newcode.scheduler.cli import handle_scheduler_start

        with (
            patch("newcode.scheduler.daemon.get_daemon_pid", return_value=123),
            patch("newcode.scheduler.cli.emit_warning"),
        ):
            assert handle_scheduler_start() is True

    def test_starts_successfully(self):
        from newcode.scheduler.cli import handle_scheduler_start

        with (
            patch("newcode.scheduler.daemon.get_daemon_pid", side_effect=[None, 456]),
            patch(
                "newcode.scheduler.daemon.start_daemon_background", return_value=True
            ),
            patch("newcode.scheduler.cli.emit_info"),
            patch("newcode.scheduler.cli.emit_success"),
        ):
            assert handle_scheduler_start() is True

    def test_fails_to_start(self):
        from newcode.scheduler.cli import handle_scheduler_start

        with (
            patch("newcode.scheduler.daemon.get_daemon_pid", return_value=None),
            patch(
                "newcode.scheduler.daemon.start_daemon_background",
                return_value=False,
            ),
            patch("newcode.scheduler.cli.emit_info"),
            patch("newcode.scheduler.cli.emit_error"),
        ):
            assert handle_scheduler_start() is False


class TestHandleSchedulerStop:
    def test_not_running(self):
        from newcode.scheduler.cli import handle_scheduler_stop

        with (
            patch("newcode.scheduler.daemon.get_daemon_pid", return_value=None),
            patch("newcode.scheduler.cli.emit_info"),
        ):
            assert handle_scheduler_stop() is True

    def test_stops_successfully(self):
        from newcode.scheduler.cli import handle_scheduler_stop

        with (
            patch("newcode.scheduler.daemon.get_daemon_pid", return_value=123),
            patch("newcode.scheduler.daemon.stop_daemon", return_value=True),
            patch("newcode.scheduler.cli.emit_info"),
            patch("newcode.scheduler.cli.emit_success"),
        ):
            assert handle_scheduler_stop() is True

    def test_fails_to_stop(self):
        from newcode.scheduler.cli import handle_scheduler_stop

        with (
            patch("newcode.scheduler.daemon.get_daemon_pid", return_value=123),
            patch("newcode.scheduler.daemon.stop_daemon", return_value=False),
            patch("newcode.scheduler.cli.emit_info"),
            patch("newcode.scheduler.cli.emit_error"),
        ):
            assert handle_scheduler_stop() is False


class TestHandleSchedulerStatus:
    def test_running_with_tasks(self):
        from newcode.scheduler.cli import handle_scheduler_status

        task = ScheduledTask(
            name="t",
            prompt="p",
            schedule_type="interval",
            schedule_value="1h",
            last_run="2024-01-01T00:00:00",
            last_status="success",
        )
        with (
            patch("newcode.scheduler.daemon.get_daemon_pid", return_value=123),
            patch("newcode.scheduler.config.load_tasks", return_value=[task]),
            patch("newcode.scheduler.cli.emit_success"),
            patch("newcode.scheduler.cli.emit_info"),
        ):
            assert handle_scheduler_status() is True

    def test_stopped_no_tasks(self):
        from newcode.scheduler.cli import handle_scheduler_status

        with (
            patch("newcode.scheduler.daemon.get_daemon_pid", return_value=None),
            patch("newcode.scheduler.config.load_tasks", return_value=[]),
            patch("newcode.scheduler.cli.emit_warning"),
            patch("newcode.scheduler.cli.emit_info"),
        ):
            assert handle_scheduler_status() is True


class TestHandleSchedulerList:
    def test_no_tasks(self):
        from newcode.scheduler.cli import handle_scheduler_list

        with (
            patch("newcode.scheduler.config.load_tasks", return_value=[]),
            patch("newcode.scheduler.cli.emit_info"),
        ):
            assert handle_scheduler_list() is True

    def test_with_tasks(self):
        from newcode.scheduler.cli import handle_scheduler_list

        task = ScheduledTask(
            name="t",
            prompt="p",
            schedule_type="interval",
            schedule_value="1h",
            last_run="2024-01-01T00:00:00",
            last_status="success",
        )
        with (
            patch("newcode.scheduler.config.load_tasks", return_value=[task]),
            patch("newcode.scheduler.cli.emit_info"),
        ):
            assert handle_scheduler_list() is True


class TestHandleSchedulerRun:
    def test_success(self):
        from newcode.scheduler.cli import handle_scheduler_run

        with (
            patch(
                "newcode.scheduler.executor.run_task_by_id",
                return_value=(True, "ok"),
            ),
            patch("newcode.scheduler.cli.emit_info"),
            patch("newcode.scheduler.cli.emit_success"),
        ):
            assert handle_scheduler_run("task-1") is True

    def test_failure(self):
        from newcode.scheduler.cli import handle_scheduler_run

        with (
            patch(
                "newcode.scheduler.executor.run_task_by_id",
                return_value=(False, "fail"),
            ),
            patch("newcode.scheduler.cli.emit_info"),
            patch("newcode.scheduler.cli.emit_error"),
        ):
            assert handle_scheduler_run("task-1") is False
