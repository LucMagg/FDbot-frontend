import typing

import discord
from discord.app_commands import Choice
from discord.ext import commands
from discord import app_commands

from service.level import LevelService
from utils.sendMessage import SendMessage

from utils.logger import Logger

class Level(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.known_levels = self.get_known_levels()

    self.level_app_command._params['name'].description = 'Nom du niveau'
    self.level_app_command._params['cost'].description = 'Coût du niveau en énergies'

    self.reward_app_command._params['level'].description = 'Nom du niveau'
    self.reward_app_command._params['type'].description = 'Type de récompense'
    self.reward_app_command._params['type'].choices = [Choice(name='gold', value=1), Choice(name='potions', value=2)]
    self.reward_app_command._params['quantity'].description = 'Quantité reçue'

    self.reward_stat_app_command._params['level'].description = 'Nom du niveau pour lequel les stats de récompenses seront affichées'


  async def level_autocompletion(self, interaction: discord.Interaction, current: str
                                 ) -> typing.List[app_commands.Choice[str]]:
    return [level for level in self.known_levels if current in level.name]

  @app_commands.command(name='level', description = 'Ajouter un niveau pour récolter des données sur ses récompenses')
  async def level_app_command(self, interaction: discord.Interaction, name: str, cost: int):
    Logger.command_log('level', interaction)
    author = str(interaction.user)
    if "spirou" not in author and "prep" not in author:
      await self.send_message.error(interaction, "Cette commande n'est pas publique pour l'instant", "Veuillez contacter Prep ou Spirou pour ajouter votre niveau à la liste.")
      Logger.ok_log('level')
      return

    await self.send_message.post(interaction)
    response = self.get_level_response(name, cost)
    await self.send_message.update(interaction, response)
    self.known_levels = self.get_known_levels()
    Logger.ok_log('level')

  def get_level_response(self, level_name, level_cost):
    print(level_name)
    print([known_level.name for known_level in self.known_levels])
    if level_name in [known_level.name for known_level in self.known_levels]:
      return {'title': f'Le niveau {level_name} existe déjà', 'description': "Tout est prêt pour l'utilisation des commandes reward et reward-stat",
              'color': 'blue'}
    level = LevelService.create_level(level_name, level_cost)

    return {'title': f'Le niveau {level.get('name')} a été ajouté', 'description': "Merci d'avoir ajouté ce niveau!",
            'color': 'blue'}

  @app_commands.autocomplete(level=level_autocompletion)
  @app_commands.command(name='reward', description='Ajouter une récompense pour un niveau')
  async def reward_app_command(self, interaction: discord.Interaction, level: str, type: Choice[int], quantity: int):
    Logger.command_log('reward', interaction)
    await self.send_message.post(interaction)
    response = self.get_reward_response(level, type.name, quantity)
    await self.send_message.update(interaction, response)
    Logger.ok_log('reward')

  @app_commands.autocomplete(level=level_autocompletion)
  @app_commands.command(name='reward-stat', description='Afficher les stats de récompense pour un niveau')
  async def reward_stat_app_command(self, interaction: discord.Interaction, level: str):
    Logger.command_log('reward-stat', interaction)
    if level not in [level.name for level in self.known_levels]:
      print("level doesn't exist")
      await self.send_message.error(interaction, "Ce niveau n'existe pas", "Veuillez choisir un niveau dans la liste ou contacter Prep ou Spirou.")
      Logger.ok_log('reward')
      return

    await self.send_message.post(interaction)
    response = self.get_reward_stat_response(level)
    await self.send_message.update(interaction, response)
    Logger.ok_log('reward')

  def get_reward_response(self, level_name, reward_type, reward_quantity):
    level = LevelService.add_reward(level_name, reward_type, reward_quantity)
    rewards = level.get('rewards')
    quantities = [f"{r.get('quantity')} {r.get('type')}: {format(r.get('appearances') / len(rewards), ".2%")}\n" for r in rewards]
    quantities_str = '\n'.join([q for q in quantities])

    return {'title': f'Récompense ajoutée au niveau {level.get('name')}', 'description': f"Merci d'avoir ajouter un récompense à ce niveau! \nStatistiques actuelles pour ce niveau:\n{quantities_str}",
            'color': 'blue'}

  def get_reward_stat_response(self, level_name):
    level = LevelService.get_level(level_name)
    rewards = level.get('rewards')
    quantities = [f"{r.get('quantity')} {r.get('type')}: {format(r.get('appearances') / len(rewards), ".2%")}\n" for r in rewards]
    quantities_str = '\n'.join([q for q in quantities])

    return {'title': f'Statistiques pour le niveau {level.get('name')}', 'description': f'Statistiques actuelles pour ce niveau:\n{quantities_str}',
            'color': 'blue'}

  def get_known_levels(self):
    levels = LevelService.get_levels()
    levels_choices = [Choice(name=l.get('name'), value=l.get('name')) for l in levels]

    return levels_choices

async def setup(bot):
  await bot.add_cog(Level(bot))