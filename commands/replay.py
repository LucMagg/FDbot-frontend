import typing
from random import choices

import discord
from discord.app_commands import Choice
from discord.ext import commands
from discord import app_commands
from service.command import CommandService
from service.interaction_handler import InteractionHandler

class Replay(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.replay_command = next((c for c in bot.static_data.commands if c['name'] == 'replay'), None)
    self.interaction_handler = InteractionHandler(self.bot)

    CommandService.init_command(self.replay_app_command, self.replay_command)
    self.event_choices = None
    self.level_choices = None
    self.view = None

  async def level_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    event = self.level_choices.get(interaction.namespace.event)
    if self.level_choices is None or event is None:
      return []
    possible_choices = await CommandService.return_autocompletion(event, current)
    return possible_choices

  async def event_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    if self.event_choices is None:
      await self.setup()
    possible_choices = await CommandService.return_autocompletion(self.event_choices, current)
    return possible_choices

  @app_commands.autocomplete(event=event_autocomplete)
  @app_commands.autocomplete(level=level_autocomplete)
  @app_commands.command(name='replay')
  async def replay_app_command(self, interaction: discord.Interaction, event: str, level: str):
    self.logger.command_log('replay', interaction)
    await self.interaction_handler.send_wait_message(interaction=interaction)

    request = {'event': event, 'level': level}
    response = await self.bot.back_requests.call('replay', False, [request], interaction)
    if not response:
      await self.get_error_response(interaction, event, level)
      return
    await self.get_replay_response(interaction, response, event, level)

  async def get_replay_response(self, interaction, resp, event, level):
    description = f"# Voici les replays pour le level {level} de l'event {event}\n"
    lines = [f"- {r.get('player')}: {r.get('link')}" for r in resp]
    for r in resp:
      await interaction.followup.send(f"{r.get('link')}`")
    description += '\n'.join(lines)

    response = {'title': '', 'description': description, 'color': 'blue'}

    await self.interaction_handler.send_embed(interaction=interaction, response=response)

    self.logger.ok_log('addreplay')

  async def get_error_response(self, interaction, event, level):
    response = {'title': '', 'description': f"# Les replays pour le level {level} de l'event {event} n'ont pas pu être trouvé", 'color': 'red'}
    await self.interaction_handler.send_embed(interaction=interaction, response=response)
    self.logger.ok_log('addreplay')

  async def setup(self, param_list=None):
    events_levels = await self.bot.back_requests.call('getReplayEventLevels', False)
    events = []
    levels_by_event = dict()
    for event in events_levels:
      events.append(Choice(name=event.get('name'), value=event.get('name')))
      levels_by_event[event.get('name')] = [Choice(name=level, value=level) for level in event.get('levels')]

    self.event_choices = events
    self.level_choices = levels_by_event

async def setup(bot):
  await bot.add_cog(Replay(bot))