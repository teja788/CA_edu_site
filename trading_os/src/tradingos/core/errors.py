"""Exception hierarchy. Every module raises subclasses of TradingOSError."""


class TradingOSError(Exception):
    """Base for all platform errors."""


class ConfigError(TradingOSError):
    """Bad or missing configuration."""


class DataError(TradingOSError):
    """Data layer failures (missing data, integrity, storage)."""


class AuthError(TradingOSError):
    """Kite auth failures, including stale access tokens."""


class RateLimitError(TradingOSError):
    """Exceeded an API rate limit even after backoff."""


class LookAheadError(TradingOSError):
    """A component attempted to read data beyond the current simulation time."""


class UniverseError(DataError):
    """Point-in-time universe data missing or inconsistent."""


class BrokerError(TradingOSError):
    """Order placement / broker API failures."""


class OrderStateError(BrokerError):
    """Illegal order state transition."""


class RiskViolation(TradingOSError):
    """A pre-trade risk check rejected an action."""


class KillSwitchActive(RiskViolation):
    """Global kill switch is engaged; no new orders permitted."""


class HoldoutLockedError(TradingOSError):
    """Attempt to evaluate on the locked out-of-sample holdout beyond quota."""
