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

    self.level_app_command._params['name'].description = 'Level name'
    self.level_app_command._params['cost'].description = 'Level energy cost'

    self.reward_app_command._params['level'].description = 'level name'
    self.reward_app_command._params['type'].description = 'reward type'
    self.reward_app_command._params['type'].choices = [Choice(name='gold', value=1), Choice(name='potions', value=2)]
    self.reward_app_command._params['quantity'].description = 'reward quantity'

    self.reward_stat_app_command._params['level'].description = 'level name for which you want stats'


  async def level_autocompletion(self, interaction: discord.Interaction, current: str
                                 ) -> typing.List[app_commands.Choice[str]]:
    return [level for level in self.known_levels if current in level.name]

  @app_commands.command(name='level', description = 'Add a level to collect stats on it')
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
    level = LevelService.create_level(level_name, level_cost)

    return {'title': f"Level {level.get('name')} added", 'description': 'Thanks for adding a new level !',
            'color': 'blue'}

  @app_commands.autocomplete(level=level_autocompletion)
  @app_commands.command(name='reward', description='Add a reward for a given level')
  async def reward_app_command(self, interaction: discord.Interaction, level: str, type: Choice[int], quantity: int):
    Logger.command_log('reward', interaction)
    await self.send_message.post(interaction)
    response = self.get_reward_response(level, type.name, quantity)
    await self.send_message.update(interaction, response)
    Logger.ok_log('reward')

  @app_commands.autocomplete(level=level_autocompletion)
  @app_commands.command(name='reward-stat', description='Get reward stats for a given level')
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
    quantities = [f"{r.get('quantity')} {r.get('type')}: {format(r.get('appearances') / len(rewards), '.2%')}\n" for r in rewards]
    quantities_str = '\n'.join([q for q in quantities])

    return {'title': f"Reward added for level {level.get('name')}", 'description': f"Thanks for adding a new reward for this level! \nCurrent stats for this level:\n{quantities_str}",
            'color': 'blue'}

  def get_reward_stat_response(self, level_name):
    level = LevelService.get_level(level_name)
    rewards = level.get('rewards')
    quantities = [f"{r.get('quantity')} {r.get('type')}: {format(r.get('appearances') / len(rewards), '.2%')}\n" for r in rewards]
    quantities_str = '\n'.join([q for q in quantities])

    return {'title': f"Reward stats for level {level.get('name')}", 'description': f"Current stats for this level:\n{quantities_str}",
            'color': 'blue'}

  def get_known_levels(self):
    levels = LevelService.get_levels()
    levels_choices = [Choice(name=l.get('name'), value=l.get('name')) for l in levels]

    return levels_choices

async def setup(bot):
  await bot.add_cog(Level(bot))