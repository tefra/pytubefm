from datetime import timedelta
from functools import partial
from typing import Optional, Tuple

import click
from tabulate import tabulate

from pytubefm.lastfm.models import PlaylistType, UserPlaylistType
from pytubefm.lastfm.params import (
    ArtistParamType,
    CountryParamType,
    TagParamType,
    UserParamType,
)
from pytubefm.lastfm.services import LastService
from pytubefm.models import (
    ConfigManager,
    History,
    PlaylistManager,
    Provider,
    TrackManager,
)
from pytubefm.utils import date


@click.group()
def lastfm():
    """Last.fm is a music service that learns what you love."""


@lastfm.group()
def add():
    """Created a playlist."""


@lastfm.command()
@click.option(
    "--api-key", help="Your last.fm api key", prompt="Last.fm Api Key"
)
def setup(api_key: str) -> None:
    """
    Configure your last.fm api account.

    Signup for a last.fm api account and use your api key in order to
    use last.fm as a playlists source for pytubefm.
    """

    if ConfigManager.get(Provider.lastfm, default=None):
        click.confirm("Overwrite existing configuration?", abort=True)

    ConfigManager.set(
        dict(provider=Provider.lastfm.value, data=dict(api_key=api_key))
    )
    click.secho("Last.fm configuration updated!")


@lastfm.command()
@click.option("--refresh", help="Refresh cache", is_flag=True, default=False)
def tags(refresh: bool):
    """List all available tags."""
    values = [
        (tag.name, tag.count, tag.reach)
        for tag in LastService.get_tags(refresh=refresh)
    ]

    click.echo_via_pager(
        tabulate(
            values, showindex=True, headers=("No", "Name", "Count", "Reach")
        )
    )


option_limit = partial(
    click.option,
    "--limit",
    help="The maximum number of tracks",
    type=click.IntRange(50, 1000),
    prompt="Maximum tracks",
    default=lambda: History.get("limit", 50),
)
option_title = partial(
    click.option, "--title", help="Custom title", prompt="Optional Title"
)


@add.command("user")
@click.option(
    "--user",
    help="The user for whom the playlist will be generated",
    prompt="Last.fm username",
    type=UserParamType(),
    default=lambda: History.get("user", default=None),
)
@click.option(
    "--playlist-type",
    help="The playlist type number",
    type=UserPlaylistType.range(),
    prompt=UserPlaylistType.choices(),
)
@option_limit()
@option_title()
def add_user_playlist(user: str, playlist_type: int, limit: int, title: str):
    """
    Add a user type playlist. This type of playlists are based on a user's
    music preference and history.

    \b
    Playlist types:
    1. User loved tracks
    2. User top tracks
    3. User recent tracks
    4. User friends recent tracks
    """
    History.set(user=user, limit=limit)
    playlist = PlaylistManager.set(
        dict(
            type=UserPlaylistType.from_choice(playlist_type),
            provider=Provider.lastfm,
            arguments=dict(username=user),
            limit=limit,
            title=title.strip(),
        )
    )
    click.secho(
        "{} playlist: {}!".format(
            "Updated" if playlist.synced else "Added", playlist.id
        )
    )


@add.command("chart")
@option_limit()
@option_title()
def add_chart_playlist(limit: int, title: str):
    """Add a top tracks playlist."""

    History.set(limit=limit)
    playlist = PlaylistManager.set(
        dict(
            type=PlaylistType.CHART,
            provider=Provider.lastfm,
            limit=limit,
            title=title.strip(),
        )
    )
    click.secho(
        "{} playlist: {}!".format(
            "Updated" if playlist.synced else "Added", playlist.id
        )
    )


@add.command("country")
@click.option(
    "--country",
    help="An alpha-2 ISO-3166 country code",
    type=CountryParamType(),
    prompt="Country Code",
)
@option_limit()
@option_title()
def add_country_playlist(country: str, limit: int, title: str):
    """Add a top tracks playlist by country."""

    History.set(limit=limit)
    playlist = PlaylistManager.set(
        dict(
            type=PlaylistType.COUNTRY,
            provider=Provider.lastfm,
            arguments=dict(country=country),
            limit=limit,
            title=title.strip(),
        )
    )
    click.secho(
        "{} playlist: {}!".format(
            "Updated" if playlist.synced else "Added", playlist.id
        )
    )


@add.command("tag")
@click.option(
    "--tag",
    help="A last.fm tag, see tags command",
    prompt="Tag",
    type=TagParamType(),
)
@option_limit()
@option_title()
def add_tag_playlist(tag: str, limit: int, title: str):
    """Add a top tracks playlist by tag."""

    History.set(limit=limit)
    playlist = PlaylistManager.set(
        dict(
            type=PlaylistType.TAG,
            provider=Provider.lastfm,
            arguments=dict(tag=tag),
            limit=limit,
            title=title.strip(),
        )
    )

    click.secho(
        "{} playlist: {}!".format(
            "Updated" if playlist.synced else "Added", playlist.id
        )
    )


@add.command("artist")
@click.option(
    "--artist", help="An artist name", prompt="Artist", type=ArtistParamType()
)
@option_limit()
@option_title()
def add_artist_playlist(artist: str, limit: int, title: str):
    """Add a top tracks playlist by artist."""

    History.set(limit=limit)
    playlist = PlaylistManager.set(
        dict(
            type=PlaylistType.ARTIST,
            provider=Provider.lastfm,
            arguments=dict(artist=artist),
            limit=limit,
            title=title.strip(),
        )
    )

    click.secho(
        "{} playlist: {}!".format(
            "Updated" if playlist.synced else "Added", playlist.id
        )
    )


@lastfm.command("list")
@click.argument("id", required=False)
def list_playlists(id: Optional[str]):
    """List all playlists or the contents of a playlist."""

    if id:
        playlist = PlaylistManager.get(id)
        click.echo_via_pager(
            tabulate(
                [
                    (
                        t.artist,
                        t.name,
                        str(timedelta(seconds=t.duration))
                        if t.duration
                        else "-",
                        t.youtube_id,
                    )
                    for t in [TrackManager.get(id) for id in playlist.tracks]
                ],
                showindex=True,
                headers=(
                    "No",
                    "Artist",
                    "Track Name",
                    "Duration",
                    "YoutubeID",
                ),
            )
        )
    else:
        click.secho(
            tabulate(
                [
                    (
                        p.id,
                        p.youtube_id,
                        p.display_type,
                        p.display_arguments,
                        p.limit,
                        date(p.modified),
                        date(p.synced),
                        date(p.uploaded),
                    )
                    for p in PlaylistManager.find(provider=Provider.lastfm)
                ],
                headers=(
                    "ID",
                    "YoutubeID",
                    "Title",
                    "Arguments",
                    "Limit",
                    "Modified",
                    "Synced",
                    "Uploaded",
                ),
            )
        )


@lastfm.command("remove")
@click.argument("ids", required=True, nargs=-1)
def remove_playlists(ids: Tuple[str]):
    """Remove one or more playlists by id."""

    click.confirm("Do you want to continue?", abort=True)
    for id in ids:
        PlaylistManager.remove(id)
        click.secho("Removed playlist: {}!".format(id))


@lastfm.command("sync")
@click.argument("ids", required=False, nargs=-1)
def sync_playlists(ids: Tuple[str]):
    """Sync one or more playlists by id, leave empty to sync all."""

    playlists = PlaylistManager.find(provider=Provider.lastfm)
    if ids:
        playlists = list(filter(lambda x: x.id in ids, playlists))

    with click.progressbar(playlists, label="Syncing playlists") as bar:
        for playlist in bar:
            tracklist = LastService.get_tracks(
                type=playlist.type, limit=playlist.limit, **playlist.arguments
            )
            track_ids = set(
                [
                    TrackManager.set(
                        dict(
                            artist=entry.artist.name,
                            name=entry.name,
                            duration=entry.duration,
                        )
                    ).id
                    for entry in tracklist
                ]
            )
            PlaylistManager.update(playlist, dict(tracks=list(track_ids)))
