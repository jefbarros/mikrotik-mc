from __future__ import annotations


class MikrotikAutomationError(Exception):
    """Base error for user-facing failures."""


class ConfigError(MikrotikAutomationError):
    pass


class SSHConnectionError(MikrotikAutomationError):
    pass


class CommandValidationError(MikrotikAutomationError, ValueError):
    pass


class CollectionError(MikrotikAutomationError):
    pass


class SanitizationError(MikrotikAutomationError):
    pass


class ReportError(MikrotikAutomationError):
    pass


class ProfileError(MikrotikAutomationError):
    pass


class RenderError(MikrotikAutomationError):
    pass


class SafetyError(MikrotikAutomationError):
    pass


class ProvisioningError(MikrotikAutomationError):
    pass

