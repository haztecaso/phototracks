import pytest
from click.testing import CliRunner

from phototracks.__main__ import main


def test_main():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert result.output == "Hello O. from phototracks\n"
