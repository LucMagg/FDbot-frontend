import discord
from discord import app_commands
import aiohttp
from typing import Optional
import traceback
from discord.ext import commands, tasks
from itertools import cycle
from config import PREFIX, LOG_FILE

from utils.static_data import StaticData
from utils.str_utils import str_to_slug

from services.logger import Logger
from services.back_requests import BackRequests
from services.command import CommandService
from services.setup_update import SetupUpdateService
from services.language import LangService
from services.message import MessageService
from services.session_manager import SessionManager
from services.loop.loop import LoopService
from services.trap import TrapService


status = cycle(['faire plaisir à Spirou', 'tchitchi Jneb', 'coacher Nox la Chaussette'])

class MyBot(commands.Bot):
  def __init__(self):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    super().__init__(command_prefix = PREFIX, intents = intents)
    
    self.static_data = StaticData()
    self.synced = False
    self.back_requests = None
    self.level_service = None
    self.update_service = None
    self.spire_service = None
    self.map_service = None
    self.merc_service = None
    self.trap_service = None
    self.logger = Logger(log_file=f'logs/{LOG_FILE}')
  
  async def build_API_url(self, guild_id: Optional[int] = None) -> str:
    if not self.application_id:
      app_info = await self.application_info()
      self.application_id = app_info.id
    if guild_id:
      url = f'https://discord.com/api/v10/applications/{self.application_id}/guilds/{guild_id}/commands'
      self.logger.log_only('info', f'Sync GUILD {guild_id}')
    else:
      url = f'https://discord.com/api/v10/applications/{self.application_id}/commands'
      self.logger.log_only('info', 'Sync GLOBAL')
    return url
      
  async def clear_global_commands(self):
    async with aiohttp.ClientSession() as session:
      url = await self.build_API_url()
      headers = {'Authorization': f'Bot {self.http.token}'}
      async with session.get(url, headers=headers) as resp:
        commands = await resp.json()
      for cmd in commands:
        await session.delete(f'{url}/{cmd.get('id')}', headers=headers)
        self.logger.log_only('info', f'Global command deleted: {cmd.get('name')}')

  async def sync_commands(self, guild_id: Optional[int] = None):
    payloads = []
    for cmd in self.tree.get_commands():
      command_data = next((c for c in self.static_data.commands if c['name'] == cmd.name), None)
      if not command_data:
        self.logger.log_only('warning', f'No JSON data for command {cmd.name}')
        continue
      try:
        payload = self.command.build_command_payload(cmd, command_data)     
        if payload:
          payloads.append(payload)
      except Exception as e:
        self.logger.log_only('error', f'Error building payload for command {cmd.name}: {e}')
    await self.send_commands_to_discord_API(payloads, guild_id)

  async def send_commands_to_discord_API(self, payloads: list[dict], guild_id: Optional[int] = None):
    async with aiohttp.ClientSession() as session:
      url = await self.build_API_url(guild_id)
      headers = {'Authorization': f'Bot {self.http.token}', 'Content-Type': 'application/json'}
      async with session.put(url, headers=headers, json=payloads) as resp:
        text = await resp.text()
        if resp.status in (200, 201):
          self.logger.bot_log('Commands synchronization done')
        else:
          self.logger.bot_log(f'Synchronization failed: {text}')

  async def on_ready(self):
    self.status_loop.start()
    self.logger.bot_log(f'Bot logged as {self.user}')
    await self.spire_ranking_loop_service.start()
    self.logger.bot_log(f'Spire ranking loop started')
    await self.spire_reminder_loop_service.start()
    self.logger.bot_log(f'Spire reminder loop started')
    await self.dc_cleaner_loop_service.start()
    self.logger.bot_log(f'DC cleaner loop started')

  async def setup_hook(self):
    self.logger.bot_log('Bot initializing...')
    self.static_data.load_all_data()
    self.logger.bot_log('All static data loaded')
    await self.load_services()
    self.logger.bot_log('Services loaded')
    self.loop.create_task(self.session_manager.cleanup_loop())
    await self.load_all_commands()
    #await self.clear_global_commands()
    if not self.synced:
      #DEV_GUILD_ID = 1119633026377318484 # <------------------------------------ /!\ FOR DEV, à supprimer pour la prod /!\ ---------------------------------------
      #await self.sync_commands(guild_id=DEV_GUILD_ID) # <--------------------------------------------------------------------------------------
      await self.sync_commands()
      self.synced = True

  async def load_services(self):
    self.logger.bot_log('Services intializing...')
    self.language = LangService(self)
    self.logger.bot_log('    Language')
    self.command = CommandService(self)
    self.logger.bot_log('    Command')
    self.session_manager = SessionManager(self)
    self.logger.bot_log('    SessionManager')
    self.message = MessageService(self)
    self.logger.bot_log('    Message')
    self.back_requests = BackRequests(self)
    self.logger.bot_log('    BackRequests')
    self.update_service = SetupUpdateService(self)
    self.logger.bot_log('    Update')
    self.spire_ranking_loop_service = LoopService(self, 'spire_ranking')
    self.logger.bot_log('    Spire Ranking Loop')
    self.spire_reminder_loop_service = LoopService(self, 'spire_reminder')
    self.logger.bot_log('    Spire Reminder Loop')
    self.dc_cleaner_loop_service = LoopService(self, 'dc_cleaner')
    self.logger.bot_log('    DC Cleaner Loop')
    self.trap_service = TrapService(self)
    self.logger.bot_log('    AntiBot Trap')
    
  async def load_all_commands(self):
    commands = [
      'addcomment', 'bothelp', 'botstats', 'classe', 'dc', 'dhjk', 'exclusive', 'hero',
      'item', 'level', 'merc', 'pet', 'reward', 'setbotlanguage', 'set_trap', 'spire', 'talent', 'update', 'xp'
    ]
    self.logger.bot_log('Commands loading...')
    for command in commands:
      try:
        cmd = f'commands.{command}'
        if cmd not in self.extensions:
          await self.load_extension(cmd)
          await self.setup_command(cmd)
          self.logger.bot_log(f'    /{command}')
      except Exception as e:
        self.logger.error_log(f'    Error while loading /{command}: {str(e)}')

  async def setup_command(self, command: str):
    existing = {cmd.name for cmd in self.tree.get_commands()}
    cog_name = command.split('.')[1].capitalize()
    cog = self.get_cog(cog_name)
    if cog:
      if hasattr(cog, 'setup'):
        await cog.setup()
      for attr in dir(cog):
        val = getattr(cog, attr)
        if isinstance(val, app_commands.Group) and val.parent is None:
          if val.name not in existing:
            self.tree.add_command(val)
            self.logger.log_only('debug', f'Group /{val.name} added to tree')

  @tasks.loop(seconds=30)
  async def status_loop(self):
    await self.change_presence(activity = discord.Game(name=f'Joue à {next(status)}'))
  
  async def on_message(self, message: discord.Message) -> None:
    if message.author == self.user:
      return
    if message.author.id == 617661648173268993 and 'paf' in str_to_slug(message.content):
      await message.reply(content='CONTREPAF!!! :rofl:')
      self.logger.bot_log('Contre-pafé :D')
    await self.process_commands(message)

  async def on_member_update(self, before: discord.Member, after: discord.Member):
    before_roles = set(r.id for r in before.roles)
    after_roles = set(r.id for r in after.roles)

    if any(tr for tr in self.trap_roles if tr in (after_roles - before_roles)):
      try:
        await after.ban(reason='Anti-bot trap')
        self.logger.log_only('info', f'[BAN] {after} ({after.id}) is banned')
      except discord.Forbidden:
        self.logger.log_only('error', f'[ERROR] Unable to ban {after}: not enough permissions')

  async def on_command_error(self, ctx, error):
    self.logger.error_log(f'Command error: {str(error)}')
    traceback.print_exception(type(error), error, error.__traceback__)
    await ctx.send(f'An error occurred while executing command: {str(error)}')