from pathlib import Path


def test_module_entrypoint_calls_cli_main():
    assert Path("src/github_activity_collector/__main__.py").read_text() == "from .cli import main\n\nmain()\n"
