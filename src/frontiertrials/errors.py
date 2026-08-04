"""Expected domain failures."""


class FrontierTrialsError(Exception):
    """Base user-facing error."""


class ValidationError(FrontierTrialsError):
    """Artifact validation failure."""


class IntegrityError(FrontierTrialsError):
    """Captured content no longer matches its recorded digest."""


class BlindingError(FrontierTrialsError):
    """A blind packet cannot be safely or consistently produced."""
