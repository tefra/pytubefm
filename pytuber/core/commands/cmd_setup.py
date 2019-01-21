import click

from pytuber.core.services import YouService
from pytuber.models import ConfigManager, Provider


@click.command("youtube")
@click.argument("client-secrets", type=click.Path(), required=True)
def setup(client_secrets: str) -> None:
    """
    Configure your youtube api credentials.

    Create a project in the Google Developers Console and obtain
    authorization credentials so pytuber can submit API requests.
    Download your `config_secret.json` and pass the path as an argument
    to this method
    """

    if ConfigManager.get(Provider.youtube, default=None):
        click.confirm("Overwrite existing configuration?", abort=True)

    credentials = YouService.authorize(client_secrets)
    ConfigManager.set(
        dict(
            provider=Provider.youtube.value,
            data=dict(
                refresh_token=credentials.refresh_token,
                token_uri=credentials.token_uri,
                client_id=credentials.client_id,
                client_secret=credentials.client_secret,
                scopes=credentials.scopes,
            ),
        )
    )
    click.secho("Youtube configuration updated!")