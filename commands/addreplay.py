import discord
import re
from discord.ext import commands
from discord import app_commands
from service.command import CommandService
from service.interaction_handler import InteractionHandler
from utils.misc_utils import nick

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
    author = nick(interaction)
    
    txt, replay_link = link.replace('\n', '').rsplit('<fnd://', 1)
    self.logger.log_only('debug', f'txt : {txt}')
    match = re.match(self.pattern, txt)
    if not match:
      await self.get_add_replay_error_response(interaction, link)
      return
    replay_link = f'fnd://{replay_link}'.replace('>','')
    self.logger.log_only('debug', f'replay_link : {replay_link}')

    event_level = match.group(1).strip()
    event, level = event_level.rsplit(' ', 1)
    if '<nobr>' in event:
      event = 'Dragonspire'
      level = f'Floor {level}'

    self.logger.log_only('debug', f'event : {event}')
    self.logger.log_only('debug', f'level : {level}')
    to_add = {
      'event': event.strip(),
      'level': level.strip(),
      'player': author,
      'replay': replay_link
    }
    await self.interaction_handler.send_wait_message(interaction=interaction)

    await self.bot.back_requests.call('addReplay', False, [to_add], interaction)
    message = f'Event : {event}\nLevel : {level}'
    await self.get_add_replay_response(interaction, event, level, author)

  async def get_add_replay_error_response(self, interaction, link):
    response = {'title': '', 'description': f'# Le replay n\'a pas pu être ajouté', 'color': 'red'}
    await self.interaction_handler.send_embed(interaction=interaction, response=response)
    self.logger.error_log('addreplay', f"Couldn't regex {link}")

  async def get_add_replay_response(self, interaction, event, level, author):
    description = '# Replay ajouté # \n'
    description += f'Merci pour ta participation {author} :thumbsup:\n'
    description += f'* Event : {event} \n'
    description += f'* Level : {level} \n'
    response = {'title': '', 'description': description, 'color': 'blue'}
    await self.interaction_handler.send_embed(interaction=interaction, response=response)
    self.logger.ok_log('addreplay')
    await self.bot.update_service.command_setup_updater(['replay'], False)


async def setup(bot):
  await bot.add_cog(AddReplay(bot))