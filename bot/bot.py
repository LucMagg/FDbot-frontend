import discord
from discord import app_commands
from discord.ext import commands, tasks
from itertools import cycle
from config import PREFIX
from utils.static_data import StaticData
from utils.str_utils import str_now
import traceback


status = cycle(['tester la v2',
                ])

class MyBot(commands.Bot):
  def __init__(self):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    super().__init__(command_prefix = PREFIX, intents = intents)
    
    self.static_data = StaticData()
    self.synced = False

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

    extensions = [
      'commands.hero',
      'commands.pet',
      'commands.addcomment'
    ]

    # Chargement des extensions
    for extension in extensions:
      try:
        if extension not in self.extensions:
          await self.load_extension(extension)
          print(f'[{str_now()}] Extension {extension} chargée')
        else:
          print(f'[{str_now()}] Extension {extension} déjà chargée')
      except Exception as e:
        print(f'[{str_now()}] Erreur lors du chargement de l\'extension {extension}: {str(e)}')

    print(f'[{str_now()}] Toutes les extensions sont chargées')
    

  @tasks.loop(seconds=30)
  async def status_loop(self):
    await self.change_presence(activity = discord.Game(name = next(status)))
  
  async def on_message(self, message: discord.Message) -> None:
    if message.author == self.user:
      return
    await self.process_commands(message)

  async def on_command_error(self, ctx, error):
      print(f'[{str_now()}] Erreur de commande: {str(error)}')
      traceback.print_exception(type(error), error, error.__traceback__)
      await ctx.send(f"Une erreur s'est produite lors de l'exécution de la commande: {str(error)}")