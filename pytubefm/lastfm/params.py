import click

from pytubefm.iso3166 import countries
from pytubefm.lastfm.services import LastService


class CountryParamType(click.ParamType):
    name = "Country Code"

    def convert(self, value, param, ctx):
        try:
            return countries[value.upper()].lower()
        except KeyError:
            self.fail("Unknown iso-3166 country code: %s" % value, param, ctx)


class TagParamType(click.ParamType):
    name = "Tag"

    def convert(self, value, param, ctx):
        try:
            return LastService.get_tag(value)
        except IndexError:
            self.fail("Unknown tag: %s" % value, param, ctx)


class ArtistParamType(click.ParamType):
    name = "Artist"

    def convert(self, value, param, ctx):
        try:
            return LastService.get_artist(value)
        except Exception:
            self.fail("Unknown artist: %s" % value, param, ctx)


class UserParamType(click.ParamType):
    name = "User"

    def convert(self, value, param, ctx):
        try:
            return LastService.get_user(value)
        except Exception:
            self.fail("Unknown user: %s" % value, param, ctx)
