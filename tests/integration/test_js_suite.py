import shutil
import subprocess

import pytest

PATTERN = "tests/js/*.test.mjs"

TOTAL = "# tests "


@pytest.fixture
def node():
    found = shutil.which("node")

    if found is None:
        pytest.skip("node is not available")

    return found


@pytest.mark.slow
def test_the_javascript_suite_passes(node, repo_root):
    completed = subprocess.run(
        [node, "--test", "--test-reporter=tap", PATTERN],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=600,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.slow
def test_the_javascript_suite_is_not_empty(node, repo_root):
    completed = subprocess.run(
        [node, "--test", "--test-reporter=tap", PATTERN],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=600,
    )

    counted = [line for line in completed.stdout.splitlines()
               if line.startswith(TOTAL)]

    assert counted != []
    assert int(counted[0].removeprefix(TOTAL)) > 100
