import os
import subprocess
import sys


def test_help_does_not_import_heavy_runtime_modules() -> None:
    code = (
        "import sys; "
        "from portrait_relay.cli import main; "
        "\ntry: main(['--help'])\nexcept SystemExit: pass\n"
        "print('HEAVY:' + ','.join(name for name in ('cv2','onnxruntime','PySide6') if name in sys.modules))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "."},
    )

    assert result.stdout.rstrip().endswith("HEAVY:")


def test_version_is_available_without_runtime_dependencies() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "portrait_relay.cli", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "Portrait Relay 0.1.0"


def test_unlabeled_output_without_acknowledgement_is_rejected() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "portrait_relay.cli", "--disclosure", "none"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "requires --acknowledge-unlabeled-output" in result.stderr
