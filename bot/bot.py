import discord
import traceback
from discord.ext import commands, tasks
from itertools import cycle
from config import PREFIX, LOG_FILE

from utils.static_data import StaticData
from utils.str_utils import str_to_slug
from utils.logger import Logger

from service.back_requests import BackRequests
from service.level import LevelService
from service.update import UpdateService
from service.spire import SpireService
from service.spireranking import SpireRankingService
from service.map import MapService
from service.merc import MercService


status = cycle(['faire plaisir à Spirou'])

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
    self.logger = Logger(log_file=f'logs/{LOG_FILE}')

  async def on_ready(self):
    if not self.synced:
      await self.tree.sync()
      self.synced = True
    self.status_loop.start()
    self.logger.bot_log(f'Bot loggé sous {self.user}')
    self.logger.bot_log('Commandes slash synchronisées')
    await self.map_service.check_maps_in_repos()
    self.logger.bot_log('Check maps ok')


  async def setup_hook(self):
    self.logger.bot_log('Initialisation du bot...')
    self.static_data.load_all_data()
    self.logger.bot_log('Toutes les données statiques sont chargées')
    await self.load_services()   
    await self.load_all_commands()

  async def load_services(self):
    self.back_requests = BackRequests(self)
    self.logger.bot_log('Initialisation du dialogue avec le back')
    self.level_service = LevelService(self)
    self.logger.bot_log('Initialisation du service Level')
    self.update_service = UpdateService(self)
    self.logger.bot_log('Initialisation du service Update')
    self.spire_service = SpireService(self)
    self.logger.bot_log('Initialisation du service Spire')
    self.spire_ranking_service = SpireRankingService(self)
    self.logger.bot_log('Initialisation du service SpireRanking')
    self.map_service = await MapService.create(self)
    self.logger.bot_log('Initialisation du service Map')
    self.merc_service = MercService(self)
    self.logger.bot_log('Initialisation du service Merc')

  async def load_all_commands(self):
    commands = [
      'commands.hero',
      'commands.pet',
      'commands.addcomment',
      'commands.talent',
      'commands.classe',
      'commands.item',
      'commands.dhjk',
      'commands.bothelp',
      'commands.botstats',
      'commands.petlist',
      'commands.update',
      'commands.level',
      'commands.rewardstat',
      'commands.reward',
      'commands.xp',
      'commands.spire',
      'commands.exclusive',
      'commands.spiredetails',
      'commands.merclist',
      'commands.mercregister',
      'commands.mercask'
      #'commands.testcommand'
    ]

    for command in commands:
      try:
        if command not in self.commands:
          await self.load_extension(command)
          await self.setup_command(command)
          self.logger.bot_log(f'Commande {command} chargée')
        else:
          self.logger.bot_log(f'Commande {command} déjà chargée')
      except Exception as e:
        self.logger.error_log(f'Erreur lors du chargement de la commande {command}: {str(e)}')

    self.logger.bot_log(f'Toutes les commandes sont chargées')
    
  async def setup_command(self, command, param_list=None):
    cog_name = command.split('.')[1].capitalize()
    cog = self.get_cog(cog_name)
    if cog and hasattr(cog, 'setup_with_bot'):
      await cog.setup_with_bot(self)
      self.logger.log_only('debug', f'Setup de la commande {command} avec bot ok')
    if cog and hasattr(cog, 'setup'):
      await cog.setup(param_list)
      self.logger.log_only('debug', f'Setup de la commande {command} ok')

  @tasks.loop(seconds=30)
  async def status_loop(self):
    await self.change_presence(activity = discord.Game(name = next(status)))
  
  async def on_message(self, message: discord.Message) -> None:
    if message.author == self.user:
      return
    if message.author.id == 617661648173268993 and 'paf' in str_to_slug(message.content):
      await message.reply(content='CONTREPAF!!! :rofl:')
      self.logger.bot_log('Contre-pafé :D')
    """if message.author.id == 570897451238817793 and message.content[0] != '/':
      embed = discord.Embed(description='# Je suis un gros nul ! #')
      embed.set_image(url='https://media1.tenor.com/m/9jP6PFL71MoAAAAd/shame-box.gif')
      await message.edit(embed=embed)"""

    """if message.author.id == 504814725020909578:
      gif_url = 'https://tenor.com/fr/view/gloves-on-im-ready-lets-do-this-glove-doctor-gif-15313441'
      await message.reply(content=f"CONTRE-DJACK!!! :fist:\n\n(<@701514411495653397> je t\'attends pour le double-tchitchi... :kissing_heart::rofl:){gif_url}")

      print(f"[{str_now()}] Contre-djack :D")"""

    await self.process_commands(message)

  async def on_command_error(self, ctx, error):
    self.logger.error_log(f'Erreur de commande: {str(error)}')
    traceback.print_exception(type(error), error, error.__traceback__)
    await ctx.send(f"Une erreur s'est produite lors de l'exécution de la commande: {str(error)}")