import os
from unittest.mock import patch

from jarvis_cli import main
from jarvis_core.network.degradation import DegradationLevel


def test_offline_flag_sets_degradation_level():
    with patch("sys.argv", ["jarvis_cli.py", "--offline", "show-run"]):
        with patch(
            "jarvis_core.network.degradation.DegradationManager.set_level"
        ) as mock_set_level:
            with patch("jarvis_cli.cmd_show_run"):  # Prevent actual run
                with patch("jarvis_core.ui.status.get_status_banner", return_value="Offline Mode"):
                    main()
                    mock_set_level.assert_called_with(DegradationLevel.OFFLINE)


def test_offline_env_var_sets_degradation_level():
    with patch.dict(os.environ, {"JARVIS_OFFLINE": "true"}):
        with patch("sys.argv", ["jarvis_cli.py", "show-run"]):
            with patch(
                "jarvis_core.network.degradation.DegradationManager.set_level"
            ) as mock_set_level:
                with patch("jarvis_cli.cmd_show_run"):
                    main()
                    mock_set_level.assert_called_with(DegradationLevel.OFFLINE)


def test_no_offline_flag():
    with patch("sys.argv", ["jarvis_cli.py", "show-run"]):
        with patch(
            "jarvis_core.network.degradation.DegradationManager.set_level"
        ) as mock_set_level:
            with patch("jarvis_cli.cmd_show_run"):
                main()
                mock_set_level.assert_not_called()
