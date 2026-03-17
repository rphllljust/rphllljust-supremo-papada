class MoodleIntegrationError(Exception):
    """Base exception for Moodle integration concerns."""


class MoodleAPIError(MoodleIntegrationError):
    """Raised when Moodle returns an application-level error."""


class MoodleConfigurationError(MoodleAPIError):
    """Raised when the Moodle integration is not configured."""


class MoodleUnsupportedFunctionError(MoodleAPIError):
    """Raised when a wsfunction is outside the approved integration scope."""


class MoodleWritebackError(MoodleAPIError):
    """Raised when a Moodle writeback operation fails."""


class MoodleAuthenticationError(MoodleAPIError):
    """Raised when Moodle rejects the provided credentials."""


class MoodleConnectionError(MoodleAPIError):
    """Raised when the connection to Moodle fails or times out."""


class MoodleUnexpectedResponseError(MoodleAPIError):
    """Raised when Moodle returns an invalid or unexpected payload."""


class MoodleRequestError(MoodleConnectionError):
    """Backward-compatible alias for request failures."""


class MoodleResponseError(MoodleUnexpectedResponseError):
    """Backward-compatible alias for invalid Moodle responses."""