from collections import namedtuple
from unittest import mock

import pydrag
from pydrag import Tag

from pytubefm import cli
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
    Playlist,
    PlaylistManager,
    Provider,
    Track,
    TrackManager,
)
from pytubefm.storage import Registry
from tests.utils import CommandTestCase

playlist = namedtuple("Playlist", ["id", "synced"])
Registry()


class CommandSetupTests(CommandTestCase):
    def test_create(self):
        self.assertIsNone(ConfigManager.get(Provider.lastfm, default=None))
        result = self.runner.invoke(cli, ["lastfm", "setup"], input="aaaa")

        expected_output = "\n".join(
            ("Last.fm Api Key: aaaa", "Last.fm configuration updated!")
        )
        self.assertEqual(0, result.exit_code)
        self.assertEqual(expected_output, result.output.strip())

        actual = ConfigManager.get(Provider.lastfm)
        self.assertDictEqual({"api_key": "aaaa"}, actual.data)

    def test_update(self):
        ConfigManager.set(
            dict(provider=Provider.lastfm, data=dict(api_key="bbbb"))
        )

        self.assertEqual(
            dict(api_key="bbbb"), ConfigManager.get(Provider.lastfm).data
        )
        result = self.runner.invoke(
            cli, ["lastfm", "setup"], input="\n".join(("aaaa", "y"))
        )

        expected_output = "\n".join(
            (
                "Last.fm Api Key: aaaa",
                "Overwrite existing configuration? [y/N]: y",
                "Last.fm configuration updated!",
            )
        )
        self.assertEqual(0, result.exit_code)
        self.assertEqual(expected_output, result.output.strip())

        actual = ConfigManager.get(Provider.lastfm)
        self.assertDictEqual({"api_key": "aaaa"}, actual.data)


class CommandAddTests(CommandTestCase):
    @mock.patch.object(UserParamType, "convert")
    @mock.patch.object(PlaylistManager, "set")
    def test_user(self, create_playlist, convert):
        convert.return_value = "bbb"
        create_playlist.return_value = Playlist(
            id=1, type=None, provider=None, limit=10
        )
        result = self.runner.invoke(
            cli,
            ["lastfm", "add", "user"],
            input="\n".join(("aaa", "2", "50", "My Favorite  ")),
            catch_exceptions=False,
        )

        expected_output = "\n".join(
            (
                "Last.fm username: aaa",
                "Playlist Types",
                "[1] user_loved_tracks",
                "[2] user_top_tracks",
                "[3] user_recent_tracks",
                "[4] user_friends_recent_tracks",
                "Select a playlist type 1-4: 2",
                "Maximum tracks [50]: 50",
                "Optional Title: My Favorite  ",
                "Added playlist: 1!",
            )
        )

        create_playlist.assert_called_once_with(
            dict(
                type=UserPlaylistType.USER_TOP_TRACKS,
                provider=Provider.lastfm,
                arguments=dict(username="bbb"),
                limit=50,
                title="My Favorite",
            )
        )
        self.assertEqual(0, result.exit_code)
        self.assertEqual(expected_output, result.output.strip())

    @mock.patch.object(PlaylistManager, "set")
    def test_chart(self, create_playlist):
        create_playlist.return_value = Playlist(
            id=1, type=None, provider=None, limit=10
        )
        result = self.runner.invoke(
            cli, ["lastfm", "add", "chart"], input="50\n "
        )

        expected_output = "\n".join(
            (
                "Maximum tracks [50]: 50",
                "Optional Title:  ",
                "Added playlist: 1!",
            )
        )
        create_playlist.assert_called_once_with(
            dict(
                type=PlaylistType.CHART,
                provider=Provider.lastfm,
                limit=50,
                title="",
            )
        )
        self.assertEqual(0, result.exit_code)
        self.assertEqual(expected_output, result.output.strip())

    @mock.patch.object(CountryParamType, "convert")
    @mock.patch.object(PlaylistManager, "set")
    def test_country(self, create_playlist, country_param_type):
        country_param_type.return_value = "greece"
        create_playlist.return_value = Playlist(
            id=1, type=None, provider=None, limit=10
        )
        result = self.runner.invoke(
            cli, ["lastfm", "add", "country"], input=b"gr\n50\n "
        )

        expected_output = "\n".join(
            (
                "Country Code: gr",
                "Maximum tracks [50]: 50",
                "Optional Title:  ",
                "Added playlist: 1!",
            )
        )
        create_playlist.assert_called_once_with(
            dict(
                type=PlaylistType.COUNTRY,
                provider=Provider.lastfm,
                arguments=dict(country="greece"),
                limit=50,
                title="",
            )
        )
        self.assertEqual(0, result.exit_code)
        self.assertEqual(expected_output, result.output.strip())

    @mock.patch.object(TagParamType, "convert")
    @mock.patch.object(PlaylistManager, "set")
    def test_tag(self, create_playlist, convert):
        convert.return_value = "rock"
        create_playlist.return_value = Playlist(
            id=1, type=None, provider=None, limit=10, synced=111
        )
        result = self.runner.invoke(
            cli, ["lastfm", "add", "tag"], input="rock\n50\n "
        )

        expected_output = "\n".join(
            (
                "Tag: rock",
                "Maximum tracks [50]: 50",
                "Optional Title:  ",
                "Updated playlist: 1!",
            )
        )
        create_playlist.assert_called_once_with(
            dict(
                type=PlaylistType.TAG,
                provider=Provider.lastfm,
                arguments=dict(tag="rock"),
                limit=50,
                title="",
            )
        )
        self.assertEqual(0, result.exit_code)
        self.assertEqual(expected_output, result.output.strip())

    @mock.patch.object(ArtistParamType, "convert")
    @mock.patch.object(PlaylistManager, "set")
    def test_artist(self, create_playlist, artist_param):
        artist_param.return_value = "Queen"
        create_playlist.return_value = Playlist(
            id=1, type=None, provider=None, limit=10
        )
        result = self.runner.invoke(
            cli,
            ["lastfm", "add", "artist"],
            input="Queen\n50\nQueen....",
            catch_exceptions=False,
        )

        expected_output = "\n".join(
            (
                "Artist: Queen",
                "Maximum tracks [50]: 50",
                "Optional Title: Queen....",
                "Added playlist: 1!",
            )
        )
        create_playlist.assert_called_once_with(
            dict(
                type=PlaylistType.ARTIST,
                provider=Provider.lastfm,
                arguments=dict(artist="Queen"),
                limit=50,
                title="Queen....",
            )
        )
        self.assertEqual(0, result.exit_code)
        self.assertEqual(expected_output, result.output.strip())


class CommandTagsTests(CommandTestCase):
    @mock.patch.object(LastService, "get_tags")
    @mock.patch.object(LastService, "__init__", return_value=None)
    def test_default(self, _, get_tags):
        get_tags.return_value = [
            Tag(name="rock", count=1, reach=2),
            Tag(name="rap", count=2, reach=4),
            Tag(name="metal", count=3, reach=6),
        ]
        result = self.runner.invoke(cli, ["lastfm", "tags"])

        expected_output = "\n".join(
            (
                "No  Name      Count    Reach",
                "----  ------  -------  -------",
                "   0  rock          1        2",
                "   1  rap           2        4",
                "   2  metal         3        6",
            )
        )
        get_tags.assert_called_once_with(refresh=False)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(expected_output, result.output.strip())

    @mock.patch.object(LastService, "get_tags")
    @mock.patch.object(LastService, "__init__", return_value=None)
    def test_force_refresh(self, _, get_tags):
        result = self.runner.invoke(cli, ["lastfm", "tags", "--refresh"])

        get_tags.assert_called_once_with(refresh=True)
        self.assertEqual(0, result.exit_code)


class CommandListPlaylistsTests(CommandTestCase):
    @mock.patch.object(PlaylistManager, "find")
    def test_list_without_id(self, find):

        find.return_value = [
            Playlist(
                type="foo",
                provider=Provider.lastfm,
                limit=10,
                youtube_id="456ybnm",
                arguments=dict(a=1),
                modified=1546727685,
            ),
            Playlist(
                type="bar",
                provider=Provider.lastfm,
                limit=15,
                arguments=dict(b=1, c=2),
                modified=1546727185,
                synced=1546727285,
                uploaded=1546727385,
            ),
        ]

        result = self.runner.invoke(cli, ["lastfm", "list"])

        expected_output = "\n".join(
            (
                "ID       YoutubeID    Title    Arguments      Limit  Modified          Synced            Uploaded",
                "-------  -----------  -------  -----------  -------  ----------------  ----------------  ----------------",
                "1ffdbf3  456ybnm      Foo      a: 1              10  2019-01-05 22:34  -                 -",
                "2884480               Bar      b: 1, c: 2        15  2019-01-05 22:26  2019-01-05 22:28  2019-01-05 22:29",
            )
        )
        find.assert_called_once_with(provider=Provider.lastfm)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(expected_output, result.output.strip())

    @mock.patch.object(TrackManager, "get")
    @mock.patch.object(PlaylistManager, "get")
    def test_list_with_id(self, get_playlists, get_track):
        playlist = Playlist(
            type="foo",
            provider=Provider.lastfm,
            limit=10,
            arguments=dict(a=1),
            tracks=[1, 2, 3],
        )

        get_playlists.return_value = playlist
        get_track.side_effect = [
            Track(name="foo", artist="bar", duration=120),
            Track(name="thug", artist="life", duration=1844),
            Track(name="nope", artist="nope", duration=0),
        ]

        result = self.runner.invoke(
            cli, ["lastfm", "list", playlist.id], catch_exceptions=False
        )

        expected_output = "\n".join(
            (
                "No  Artist    Track Name    Duration    YoutubeID",
                "----  --------  ------------  ----------  -----------",
                "   0  bar       foo           0:02:00",
                "   1  life      thug          0:30:44",
                "   2  nope      nope          -",
            )
        )
        get_track.assert_has_calls([mock.call(id) for id in playlist.tracks])
        self.assertEqual(0, result.exit_code)
        self.assertEqual(expected_output, result.output.strip())


class CommandRemovePlaylistTests(CommandTestCase):
    @mock.patch.object(PlaylistManager, "remove")
    def test_remove(self, remove):

        result = self.runner.invoke(
            cli, ["lastfm", "remove", "foo", "bar"], input="y"
        )

        expected_output = "\n".join(
            (
                "Do you want to continue? [y/N]: y",
                "Removed playlist: foo!",
                "Removed playlist: bar!",
            )
        )
        self.assertEqual(0, result.exit_code)
        self.assertEqual(expected_output, result.output.strip())
        remove.assert_has_calls([mock.call("foo"), mock.call("bar")])

    def test_remove_no_confirm(self):
        result = self.runner.invoke(
            cli, ["lastfm", "remove", "foo"], input="n"
        )

        expected_output = "\n".join(
            ("Do you want to continue? [y/N]: n", "Aborted!")
        )
        self.assertEqual(1, result.exit_code)
        self.assertEqual(expected_output, result.output.strip())


class CommandSyncPlaylistsTests(CommandTestCase):
    @mock.patch.object(TrackManager, "set")
    @mock.patch.object(LastService, "get_tracks")
    @mock.patch.object(PlaylistManager, "update")
    @mock.patch.object(PlaylistManager, "find")
    def test_sync_all(self, find, update, get_tracks, set):
        tracks = {}
        set_side_effects = []
        for ltr in "abcdef":
            tracks[ltr] = pydrag.Track.from_dict(
                dict(name=ltr, artist="@%s" % ltr)
            )
            set_side_effects.append(
                Track(name=ltr, artist="@%s" % ltr, id=ord(ltr) - 96)
            )

        set.side_effect = set_side_effects
        playlist_one = Playlist(
            type="foo",
            provider=Provider.lastfm,
            limit=10,
            arguments=dict(a=1),
            modified=1546727685,
        )
        playlist_two = Playlist(
            type="bar",
            provider=Provider.lastfm,
            limit=15,
            arguments=dict(b=1, c=2),
            modified=1546727185,
            synced=1546727285,
            uploaded=1546727385,
        )

        find.return_value = [playlist_one, playlist_two]
        get_tracks.side_effect = [
            [tracks.get("a"), tracks.get("b"), tracks.get("c")],
            [tracks.get("d"), tracks.get("e"), tracks.get("f")],
        ]

        result = self.runner.invoke(
            cli, ["lastfm", "sync"], catch_exceptions=False
        )

        self.assertEqual(0, result.exit_code)
        find.assert_called_once_with(provider=Provider.lastfm)
        get_tracks.assert_has_calls(
            [
                mock.call(type="foo", limit=10, a=1),
                mock.call(type="bar", limit=15, b=1, c=2),
            ]
        )
        set.assert_has_calls(
            [
                mock.call({"artist": "@a", "name": "a", "duration": None}),
                mock.call({"artist": "@b", "name": "b", "duration": None}),
                mock.call({"artist": "@c", "name": "c", "duration": None}),
                mock.call({"artist": "@d", "name": "d", "duration": None}),
                mock.call({"artist": "@e", "name": "e", "duration": None}),
                mock.call({"artist": "@f", "name": "f", "duration": None}),
            ]
        )

        update.assert_has_calls(
            [
                mock.call(playlist_one, dict(tracks=[1, 2, 3])),
                mock.call(playlist_two, dict(tracks=[4, 5, 6])),
            ]
        )

    @mock.patch.object(TrackManager, "set")
    @mock.patch.object(LastService, "get_tracks")
    @mock.patch.object(PlaylistManager, "update")
    @mock.patch.object(PlaylistManager, "find")
    def test_sync_one(self, find, update, get_tracks, set):
        tracks = {}
        set_side_effects = []
        for ltr in "def":
            tracks[ltr] = pydrag.Track.from_dict(
                dict(name=ltr, artist="@%s" % ltr)
            )
            set_side_effects.append(
                Track(name=ltr, artist="@%s" % ltr, id=ord(ltr) - 96)
            )

        set.side_effect = set_side_effects
        playlist_one = Playlist(
            type="foo",
            provider=Provider.lastfm,
            limit=10,
            arguments=dict(a=1),
            modified=1546727685,
        )
        playlist_two = Playlist(
            type="bar",
            provider=Provider.lastfm,
            limit=15,
            arguments=dict(b=1, c=2),
            modified=1546727185,
            synced=1546727285,
            uploaded=1546727385,
        )

        find.return_value = [playlist_one, playlist_two]
        get_tracks.side_effect = [
            [tracks.get("d"), tracks.get("e"), tracks.get("f")]
        ]

        result = self.runner.invoke(
            cli, ["lastfm", "sync", playlist_two.id], catch_exceptions=False
        )

        self.assertEqual(0, result.exit_code)
        find.assert_called_once_with(provider=Provider.lastfm)
        get_tracks.assert_called_once_with(type="bar", limit=15, b=1, c=2)
        set.assert_has_calls(
            [
                mock.call({"artist": "@d", "name": "d", "duration": None}),
                mock.call({"artist": "@e", "name": "e", "duration": None}),
                mock.call({"artist": "@f", "name": "f", "duration": None}),
            ]
        )

        update.assert_called_once_with(playlist_two, dict(tracks=[4, 5, 6]))
