import discord
from discord.ext import commands, tasks
from itertools import cycle
from config import PREFIX
from utils.levelData import LevelData
from utils.static_data import StaticData
from utils.str_utils import str_now, str_to_slug
from service.back_requests import BackRequests
import traceback


status = cycle(['faire plaisir à Spirou'])

class MyBot(commands.Bot):
  def __init__(self):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    super().__init__(command_prefix = PREFIX, intents = intents)
    
    self.static_data = StaticData()
    self.synced = False
    self.level_data = LevelData()
    self.back_requests = None

  async def on_ready(self):
    await self.wait_until_ready()
    if not self.synced:
      await self.tree.sync()
      self.synced = True
    self.status_loop.start()
    print(f'[{str_now()}] Bot loggé sous {self.user}')
    print(f'[{str_now()}] Commandes slash synchronisées')


  async def setup_hook(self):
    print(f'[{str_now()}] Initialisation du bot...')
    self.static_data.load_all_data()
    print(f'[{str_now()}] Toutes les données statiques sont chargées')
    self.level_data.load_levels()
    print(f'[{str_now()}] Toutes les données levels sont chargées')
    self.back_requests = BackRequests(self)
    print(f'[{str_now()}] Initialisation du dialogue avec le back')

    extensions = [
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
    ]

    # Chargement des extensions
    for extension in extensions:
      try:
        if extension not in self.extensions:
          await self.load_extension(extension)
          await self.setup_extension(extension)
          print(f'[{str_now()}] Extension {extension} chargée')
        else:
          print(f'[{str_now()}] Extension {extension} déjà chargée')
      except Exception as e:
        print(f'[{str_now()}] Erreur lors du chargement de l\'extension {extension}: {str(e)}')

    print(f'[{str_now()}] Toutes les extensions sont chargées')
    
  async def setup_extension(self, extension):
    cog_name = extension.split('.')[1].capitalize()
    cog = self.get_cog(cog_name)
    if cog and hasattr(cog, 'setup'):
      await cog.setup()

  @tasks.loop(seconds=30)
  async def status_loop(self):
    await self.change_presence(activity = discord.Game(name = next(status)))
  
  async def on_message(self, message: discord.Message) -> None:
    if message.author == self.user:
      return
    if message.author.id == 617661648173268993 and 'paf' in str_to_slug(message.content):
      await message.reply(content='CONTREPAF!!! :rofl:')
      print(f"[{str_now()}] Contre-pafé :D")

    """if message.author.id == 504814725020909578:
      gif_url = 'https://tenor.com/fr/view/gloves-on-im-ready-lets-do-this-glove-doctor-gif-15313441'
      await message.reply(content=f"CONTRE-DJACK!!! :fist:\n\n(<@701514411495653397> je t\'attends pour le double-tchitchi... :kissing_heart::rofl:){gif_url}")

      print(f"[{str_now()}] Contre-djack :D")"""

    await self.process_commands(message)

  async def on_command_error(self, ctx, error):
    print(f'[{str_now()}] Erreur de commande: {str(error)}')
    traceback.print_exception(type(error), error, error.__traceback__)
    await ctx.send(f"Une erreur s'est produite lors de l'exécution de la commande: {str(error)}")