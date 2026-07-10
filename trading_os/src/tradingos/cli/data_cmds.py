"""data CLI commands (typer sub-app). Commands are added as modules land.

Heavy imports are deferred inside each command so ``platform --help`` stays
instant, mirroring the other cli/ modules.
"""

from __future__ import annotations

from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True)


@app.command()
def login(
    no_browser: Annotated[
        bool,
        typer.Option(
            "--no-browser",
            help="Print the Kite login URL instead of opening a browser (e.g. on a "
            "headless box); the local callback server still captures the redirect.",
        ),
    ] = False,
    totp: Annotated[
        bool,
        typer.Option(
            "--totp",
            help="Use the unofficial TOTP-assisted login (needs TOS_KITE_USER_ID / "
            "TOS_KITE_PASSWORD / TOS_KITE_TOTP_SECRET) instead of the interactive "
            "redirect flow.",
        ),
    ] = False,
) -> None:
    """Obtain today's Kite access token and cache it (tokens expire daily).

    The morning pre-open step for paper --schedule and live sessions; see
    docs/runbook.md section 3.
    """
    from tradingos.config.settings import get_settings
    from tradingos.core.errors import AuthError
    from tradingos.data.auth import KiteAuth

    settings = get_settings()
    auth = KiteAuth(settings)
    try:
        if totp:
            auth.totp_login()
        else:
            auth.interactive_login(open_browser=not no_browser)
    except AuthError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    # Never print the token itself -- only where it was cached.
    typer.echo(f"access token cached for today at {settings.token_cache_path}")
