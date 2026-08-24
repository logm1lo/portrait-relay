from pathlib import Path

from portrait_relay.workspace import JobWorkspace, WorkspaceRegistry


def test_context_manager_removes_only_its_workspace(tmp_path: Path) -> None:
    target = tmp_path / "clip.mp4"
    with JobWorkspace(target) as workspace:
        root = workspace.root
        (root / "frame.png").write_bytes(b"frame")
        assert workspace.output_path == root / "temp.mp4"

    assert not root.exists()
    assert not root.parent.exists()


def test_keep_frames_retains_workspace(tmp_path: Path) -> None:
    workspace = JobWorkspace(tmp_path / "clip.mp4", keep_frames=True)
    root = workspace.root

    workspace.close()
    workspace.close()

    assert root.is_dir()


def test_registry_reuses_active_job_and_separates_targets(tmp_path: Path) -> None:
    registry = WorkspaceRegistry()
    first = tmp_path / "one" / "clip.mp4"
    second = tmp_path / "two" / "clip.mp4"
    first.parent.mkdir()
    second.parent.mkdir()

    first_workspace = registry.get_or_create(first)
    assert registry.get_or_create(first) is first_workspace
    second_workspace = registry.get_or_create(second)
    assert second_workspace.root != first_workspace.root

    registry.release(first)
    assert not first_workspace.root.exists()
    assert second_workspace.root.exists()
    registry.release(second)


def test_releasing_unknown_job_is_a_noop(tmp_path: Path) -> None:
    WorkspaceRegistry().release(tmp_path / "missing.mp4")
