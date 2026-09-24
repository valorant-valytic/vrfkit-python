from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from .errors import (
    VrfkitDownloadError,
    VrfkitIntegrityError,
)

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
    archive_name = f"vrfkit-{tag}-windows-x64.zip"
    release_url = (
        f"https://github.com/{_REPOSITORY}/releases/download/{tag}"
    )

    install_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        dir=install_dir.parent,
        prefix=f".{tag}-",
    ) as temporary_directory:
        temporary_path = Path(temporary_directory)
        archive_path = temporary_path / archive_name
        checksum_path = temporary_path / f"{archive_name}.sha256"
        extracted_path = temporary_path / "install"

        _download(f"{release_url}/{archive_name}", archive_path)
        _download(
            f"{release_url}/{archive_name}.sha256",
            checksum_path,
        )
        _verify_checksum(archive_path, checksum_path)
        _extract_executable(archive_path, extracted_path)

        try:
            install_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(
                extracted_path / _EXECUTABLE_NAME,
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


def _verify_checksum(
    archive_path: Path,
    checksum_path: Path,
) -> None:
    try:
        expected = checksum_path.read_text("utf-8").split()[0].lower()
    except (OSError, IndexError) as error:
        raise VrfkitIntegrityError(
            "The release checksum file is invalid"
        ) from error

    digest = hashlib.sha256()

    try:
        with archive_path.open("rb") as archive:
            for chunk in iter(lambda: archive.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise VrfkitIntegrityError(
            "Could not read the downloaded release archive"
        ) from error

    actual = digest.hexdigest()

    if actual != expected:
        raise VrfkitIntegrityError(
            f"Release checksum mismatch: expected {expected}, got {actual}"
        )


def _extract_executable(
    archive_path: Path,
    destination: Path,
) -> None:
    try:
        with zipfile.ZipFile(archive_path) as archive:
            member = archive.getinfo(_EXECUTABLE_NAME)
            destination.mkdir(parents=True)
            archive.extract(member, destination)
    except (KeyError, OSError, zipfile.BadZipFile) as error:
        raise VrfkitDownloadError(
            "The release archive does not contain a valid vrfkit.exe"
        ) from error
