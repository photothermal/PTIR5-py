"""Exception types for the ptir5 library."""

from __future__ import annotations


class PTIR5Error(Exception):
    """Base exception for all ptir5 errors."""


class FileClosedError(PTIR5Error):
    """Raised when attempting to access data from a closed PTIR5 file."""


class InvalidMeasurementError(PTIR5Error):
    """Raised when a measurement has invalid or unreadable data."""


class MeasurementNotFoundError(PTIR5Error, KeyError):
    """Raised when a measurement GUID is not found."""
