from __future__ import annotations

import subprocess
from pathlib import Path
from os import PathLike

from .errors import VrfkitExportError
from .installer import resolve_executable


class Vrfkit:
    """Client for a downloaded vrfkit release.

    Args:
        version:
            Release tag to use, such as ``"v0.2.0"`` or ``"0.2.0"``.
            Use ``"latest"`` to resolve the latest GitHub release.

    The executable is downloaded lazily when this object is created and
    cached outside the current project.
    """

    def __init__(self, version: str = "latest") -> None:
        if not version:
            raise ValueError("version cannot be empty")

        self._version, self._executable = resolve_executable(version)

    @property
    def version(self) -> str:
        """The resolved GitHub release tag."""

        return self._version

    def export(
        self,
        replay_path: PathLike,
        output_dir: PathLike,
    ) -> None:
        """Export a replay to a directory.

        Args:
            replay_path:
                Path to an existing ``.vrf`` replay.
            output_dir:
                Directory in which vrfkit should write its output.

        Raises:
            FileNotFoundError:
                If ``replay_path`` does not exist.
            ValueError:
                If ``replay_path`` is not a file.
            VrfkitExportError:
                If the vrfkit process exits unsuccessfully.
        """

        replay = Path(replay_path).expanduser().resolve()
        output = Path(output_dir).expanduser().resolve()

        if not replay.exists():
            raise FileNotFoundError(replay)

        if not replay.is_file():
            raise ValueError(f"Replay path is not a file: {replay}")

        output.mkdir(parents=True, exist_ok=True)

        process = subprocess.run(
            [
                str(self._executable),
                "export",
                str(replay),
                "--out",
                str(output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if process.returncode != 0:
            raise VrfkitExportError(
                f"vrfkit failed to export {replay}",
                returncode=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
            )
