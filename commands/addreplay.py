import discord
import re
from discord.ext import commands
from discord import app_commands
from service.command import CommandService
from service.interaction_handler import InteractionHandler

class AddReplay(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.replay_command = next((c for c in bot.static_data.commands if c['name'] == 'addreplay'), None)
    self.interaction_handler = InteractionHandler(self.bot)

    self.pattern = r"^Shared a Replay:(.*?)$"

    CommandService.init_command(self.replay_app_command, self.replay_command)
    self.view = None

  @app_commands.command(name='addreplay')
  async def replay_app_command(self, interaction: discord.Interaction, link: str):
    self.logger.command_log('addreplay', interaction)
    author = str(interaction.user)

    txt, replay_link = link.rsplit(" ", 1)
    match = re.match(self.pattern, txt)
    if not match:
      await self.get_add_replay_error_response(interaction, link)
      return

    event, level = None, None
    if match:
      event_level = match.group(1)

      event, level = event_level.rsplit(" ", 1)

    to_add = {
      'event': event.strip(),
      'level': level.strip(),
      'player': author,
      'replay': replay_link
    }
    await self.interaction_handler.send_wait_message(interaction=interaction)

    await self.bot.back_requests.call('addReplay', False, [to_add], interaction)
    await self.get_add_replay_response(interaction)

  async def get_add_replay_error_response(self, interaction, link):
    response = {'title': '', 'description': f"# Le replay n'a pas pu être ajouté", 'color': 'red'}
    await self.interaction_handler.send_embed(interaction=interaction, response=response)
    self.logger.error_log('addreplay', f"Couldn't regex {link}")

  async def get_add_replay_response(self, interaction):
    response = {'title': '', 'description': f"# Merci d'avoir ajouté ce replay :wink:", 'color': 'blue'}
    await self.interaction_handler.send_embed(interaction=interaction, response=response)
    self.logger.ok_log('addreplay')
    await self.bot.update_service.command_setup_updater(['replay'], False)


async def setup(bot):
  await bot.add_cog(AddReplay(bot))