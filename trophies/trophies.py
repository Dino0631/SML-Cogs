# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017 SML

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from enum import Enum

from __main__ import send_cmd_help
from cogs.utils import checks
from cogs.utils.dataIO import dataIO
from discord.ext import commands
from random import choice
import discord

import os

PATH = os.path.join("data", "trophies")
JSON = os.path.join(PATH, "settings.json")

set_allowed_role = 'Bot Commander'
bs_set_allowed_roles = ['Bot Commander', 'BS-Co-Leader']


class ClanType:
    """Type of trophies."""
    CR = "CR"
    BS = "BS"


RACF_CLANS = {
    ClanType.CR: [
        'Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo',
        'Foxtrot', 'Golf', 'Hotel', 'eSports'],
    ClanType.BS: ['Alpha', 'Bravo', 'Charlie', 'Delta']
}

SERVER_DEFAULTS = {
    "ServerName": None,
    "ServerID": None,
    "Trophies": {
        ClanType.CR: [],
        ClanType.BS: []
    }
}


class Trophies:
    """
    Display the current trophy requirements for RACF.

    Note: RACF specific plugin for Red
    """

    def __init__(self, bot):
        """Init."""
        self.bot = bot
        self.settings = dataIO.load_json(JSON)

    @checks.serverowner_or_permissions(manage_server=True)
    @commands.group(pass_context=True, no_pm=True)
    async def settrophies(self, ctx):
        """Set trophies settings."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @settrophies.command(name="initserver", pass_context=True)
    async def settrophies_initserver(self, ctx, init_all=False):
        """Initialize server settings to default values.

        Requires confirmation as this is a destructive process.
        """
        server = ctx.message.server
        if init_all:
            self.settings = {}

        server_settings = SERVER_DEFAULTS.copy()
        server_settings["ServerName"] = server.name
        server_settings["ServerID"] = server.id
        for clan in RACF_CLANS[ClanType.CR]:
            server_settings['Trophies'][ClanType.CR].append({
                'name': clan,
                'value': 0
            })
        for clan in RACF_CLANS[ClanType.BS]:
            server_settings['Trophies'][ClanType.BS].append({
                'name': clan,
                'value': 0
            })

        self.settings[server.id] = server_settings

        dataIO.save_json(JSON, self.settings)
        await self.bot.say(
            'Settings set to server defaults.')

    @commands.group(aliases=["tr"], pass_context=True, no_pm=True)
    async def trophies(self, ctx):
        """Display RACF Trophy requirements."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @trophies.command(name="show", pass_context=True, no_pm=True)
    async def trophies_show(self, ctx):
        """Display the requirements."""
        server = ctx.message.server
        data = self.embed_trophies(server, ClanType.CR)
        await self.bot.say(embed=data)

    @trophies.command(name="set", pass_context=True, no_pm=True)
    @commands.has_role(set_allowed_role)
    async def trophies_set(self, ctx, clan: str, *, req: str):
        """Set the trophy requirements for clans."""
        await self.run_trophies_set(ctx, ClanType.CR, clan, req)

    @commands.group(aliases=["bstr"], pass_context=True, no_pm=True)
    async def bstrophies(self, ctx):
        """Display RACF Trophy requirements."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @bstrophies.command(name="show", pass_context=True, no_pm=True)
    async def bstrophies_show(self, ctx):
        """Display the requirements."""
        server = ctx.message.server
        data = self.embed_trophies(server, ClanType.BS)
        await self.bot.say(embed=data)

    @bstrophies.command(name="set", pass_context=True, no_pm=True)
    @commands.has_any_role(*bs_set_allowed_roles)
    async def bstrophies_set(self, ctx, clan: str, *, req: str):
        """Set the trophy requirements for clans."""
        await self.run_trophies_set(ctx, ClanType.BS, clan, req)

    async def run_trophies_set(self, ctx, clan_type, clan: str, req: str):
        """Set to trophy requirements for clans."""
        server = ctx.message.server
        clans = RACF_CLANS[clan_type]

        if clan.lower() not in [c.lower() for c in clans]:
            await self.bot.say("Clan name is not valid.")
            return

        for i, c in enumerate(clans):
            if clan.lower() == c.lower():
                self.settings[server.id][
                    "Trophies"][clan_type][i]["value"] = req
                await self.bot.say(
                    "Trophy requirement for {} "
                    "updated to {}.".format(clan, req))
                break

        dataIO.save_json(JSON, self.settings)

    def embed_trophies(self, server, clan_type):
        """Return Discord embed."""
        color = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        color = int(color, 16)

        if clan_type == ClanType.CR:
            our_clans = 'Clash Royale clans'
        else:
            our_clans = 'Brawl Stars bands'

        description = (
            "Minimum trophies to join our {}. "
            "Current trophies required."
        ).format(our_clans)

        data = discord.Embed(
            color=discord.Color(value=color),
            title="Trophy requirements",
            description=description
        )

        clans = self.settings[server.id]["Trophies"][clan_type]

        for clan in clans:
            name = clan["name"]
            value = clan["value"]

            if str(value).isdigit():
                value = '{:,}'.format(int(value))

            data.add_field(name=str(name), value=value)

        if server.icon_url:
            data.set_author(name=server.name, url=server.icon_url)
            data.set_thumbnail(url=server.icon_url)
        else:
            data.set_author(name=server.name)

        return data


def check_folder():
    """Check folder."""
    if not os.path.exists(PATH):
        os.makedirs(PATH)


def check_file():
    """Check files."""
    if not dataIO.is_valid_json(JSON):
        dataIO.save_json(JSON, {})


def setup(bot):
    """Setup bot."""
    check_folder()
    check_file()
    n = Trophies(bot)
    bot.add_cog(n)


