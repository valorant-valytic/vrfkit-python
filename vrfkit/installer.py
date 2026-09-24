from __future__ import annotations

import json
import os
import shutil
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from .errors import VrfkitDownloadError

_REPOSITORY = "Matthias1590/vrfkit"
_EXECUTABLE_NAME = "vrfkit.exe"


def resolve_executable(version: str) -> tuple[str, Path]:
    tag = _resolve_tag(version)
    install_dir = _cache_root() / tag
    executable = install_dir / _EXECUTABLE_NAME

    if executable.is_file():
        return tag, executable

    _install_release(tag, install_dir)
    return tag, executable


def _resolve_tag(version: str) -> str:
    if version != "latest":
        return version if version.startswith("v") else f"v{version}"

    request = urllib.request.Request(
        f"https://api.github.com/repos/{_REPOSITORY}/releases/latest",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "vrfkit-python",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            payload = json.load(response)
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise VrfkitDownloadError(
            "Could not resolve the latest vrfkit release"
        ) from error

    tag = payload.get("tag_name")
    if not isinstance(tag, str) or not tag:
        raise VrfkitDownloadError(
            "The latest GitHub release did not contain a valid tag"
        )

    return tag


def _cache_root() -> Path:
    if local_app_data := os.getenv("LOCALAPPDATA"):
        return Path(local_app_data) / "vrfkit"

    return Path.home() / ".cache" / "vrfkit"


def _install_release(tag: str, install_dir: Path) -> None:
    release_url = (
        f"https://github.com/{_REPOSITORY}/releases/download/{tag}"
    )

    install_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        dir=install_dir.parent,
        prefix=f".{tag}-",
    ) as temporary_directory:
        executable_path = (
            Path(temporary_directory) / _EXECUTABLE_NAME
        )

        _download(
            f"{release_url}/{_EXECUTABLE_NAME}",
            executable_path,
        )

        try:
            install_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(
                executable_path,
                install_dir / _EXECUTABLE_NAME,
            )
        except OSError as error:
            raise VrfkitDownloadError(
                f"Could not install vrfkit into {install_dir}"
            ) from error


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "vrfkit-python"},
    )

    try:
        with (
            urllib.request.urlopen(request) as response,
            destination.open("wb") as output,
        ):
            shutil.copyfileobj(response, output)
    except (urllib.error.URLError, OSError) as error:
        raise VrfkitDownloadError(
            f"Could not download {url}"
        ) from error
