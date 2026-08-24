from pathlib import Path

import modules.globals
from modules.utilities import clean_temp, create_temp, get_temp_directory_path


def test_jobs_with_same_basename_get_distinct_workspaces(tmp_path: Path) -> None:
    first_target = tmp_path / "first" / "clip.mp4"
    second_target = tmp_path / "second" / "clip.mp4"
    first_target.parent.mkdir()
    second_target.parent.mkdir()
    modules.globals.keep_frames = False

    create_temp(str(first_target))
    create_temp(str(second_target))
    first_workspace = Path(get_temp_directory_path(str(first_target)))
    second_workspace = Path(get_temp_directory_path(str(second_target)))

    assert first_workspace != second_workspace
    assert first_workspace.is_dir()
    assert second_workspace.is_dir()

    clean_temp(str(first_target))
    assert not first_workspace.exists()
    assert second_workspace.exists()
    clean_temp(str(second_target))
