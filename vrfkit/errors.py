class VrfkitError(Exception):
    """Base exception for all vrfkit wrapper failures."""


class VrfkitDownloadError(VrfkitError):
    """Raised when a vrfkit release cannot be downloaded or extracted."""


class VrfkitIntegrityError(VrfkitDownloadError):
    """Raised when a downloaded release fails integrity verification."""


class VrfkitExportError(VrfkitError):
    """Raised when vrfkit fails to export a replay."""

    def __init__(
        self,
        message: str,
        *,
        returncode: int,
        stdout: str,
        stderr: str,
    ) -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
