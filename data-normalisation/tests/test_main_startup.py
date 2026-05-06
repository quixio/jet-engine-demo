import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch, MagicMock


def _make_mock_app():
    """Return a (mock_app, mock_sdf) pair where SDF methods chain back to itself."""
    mock_app = MagicMock()
    mock_sdf = MagicMock()
    mock_app.dataframe.return_value = mock_sdf
    mock_sdf.print.return_value = mock_sdf
    mock_sdf.apply.return_value = mock_sdf
    mock_sdf.filter.return_value = mock_sdf
    mock_sdf.set_timestamp.return_value = mock_sdf
    mock_sdf.to_topic.return_value = mock_sdf
    return mock_app, mock_sdf


@patch('main.Application')
def test_main_starts_without_dead_letter_env_var(mock_app_class):
    """main() must not raise when dead_letter_topic env var is absent."""
    mock_app, _ = _make_mock_app()
    mock_app_class.return_value = mock_app

    env = {"input": "raw-data", "output": "normalised-data"}
    with patch.dict(os.environ, env, clear=True):
        from main import main
        main()

    mock_app.run.assert_called_once()
    # Only input and output topics should be created — no DLQ topic
    assert mock_app.topic.call_count == 2
    topic_names = [
        c.kwargs.get('name', c.args[0] if c.args else None)
        for c in mock_app.topic.call_args_list
    ]
    assert "raw-data" in topic_names
    assert "normalised-data" in topic_names


@patch('main.Application')
def test_main_wires_dead_letter_topic_when_set(mock_app_class):
    """main() must call app.topic() for the DLQ name when env var is present."""
    mock_app, _ = _make_mock_app()
    mock_app_class.return_value = mock_app

    env = {
        "input": "raw-data",
        "output": "normalised-data",
        "dead_letter_topic": "dead-letter-queue",
    }
    with patch.dict(os.environ, env, clear=True):
        from main import main
        main()

    mock_app.run.assert_called_once()
    # input, output, and DLQ topics should all be created
    assert mock_app.topic.call_count == 3
    topic_names = [
        c.kwargs.get('name', c.args[0] if c.args else None)
        for c in mock_app.topic.call_args_list
    ]
    assert "dead-letter-queue" in topic_names
