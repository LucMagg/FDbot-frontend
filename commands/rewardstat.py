import typing
import requests
import discord

from discord.ext import commands
from discord import app_commands

from service.command import CommandService

from utils.sendMessage import SendMessage
from utils.logger import Logger
from utils.misc_utils import pluriel
from config import DB_PATH

class RewardStat(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.send_message = SendMessage(self.bot)
    self.level_data = bot.level_data
    self.reward_stat_command = next((c for c in bot.static_data.commands if c['name'] == 'reward-stat'), None)
    self.gear_qualities = [g for g in bot.static_data.qualities if g['type'] == 'gear']
    self.dust_qualities = bot.static_data.dusts

    CommandService.init_command(self.reward_stat_app_command, self.reward_stat_command)

  async def level_autocompletion(self, interaction: discord.Interaction, current: str
                                 ) -> typing.List[app_commands.Choice[str]]:
    return [level for level in self.level_data.known_levels if current in level.name][:25]

  def get_potion_emoji(self, guild):
    potion_emoji = discord.utils.get(guild.emojis, name='potion')
    return str(potion_emoji) if potion_emoji else ''

  def get_rewards_str(self, rewards, guild):
    total_reward_appearances = sum([reward.get('appearances') for reward in rewards])
    quantities = []
    for r in rewards:
      match r.get('type'):
        case 'gold':
          icon = ':moneybag:'
        case 'gear':
          icon = next((g.get('icon') for g in self.gear_qualities if g.get('name') == r.get('quality')), None)
        case 'dust':
          icon = next((d.get('icon') for d in self.dust_qualities if d.get('name') == r.get('quality')), None)
        case 'potions':
          icon = self.get_potion_emoji(guild)

      quantities.append(f"{icon} {r.get('quantity')} {r.get('quality', '')} {r.get('type')}: {format(r.get('appearances') / total_reward_appearances, '.2%')} ({r.get('appearances')})\n")
    return f'{total_reward_appearances} récompense{pluriel(total_reward_appearances)} recueillie{pluriel(total_reward_appearances)}:\n' + '\n'.join([q for q in quantities])

  @app_commands.autocomplete(level=level_autocompletion)
  @app_commands.command(name='reward-stat')
  async def reward_stat_app_command(self, interaction: discord.Interaction, level: str):
    Logger.command_log('reward-stat', interaction)
    if level not in [level.name for level in self.level_data.known_levels]:
      await self.send_message.error(interaction, "Ce niveau n'existe pas", "Veuillez choisir un niveau dans la liste ou contacter Prep ou Spirou.")
      Logger.ok_log('reward-stat')
      return

    await self.send_message.post(interaction)
    response = self.get_reward_stat_response(level, interaction.guild)
    await self.send_message.update(interaction, response)
    Logger.ok_log('reward-stat')

  def get_reward_stat_response(self, level_name, guild):
    level = self.get_level(level_name)
    quantities_str = self.get_rewards_str(level.get('rewards', []), guild)

    return {'title': f'Statistiques pour le niveau {level.get('name')}', 'description': f'Statistiques actuelles pour ce niveau:\n{quantities_str}',
            'color': 'blue'}

  def get_level(self, level_name):
    return requests.get(f"{DB_PATH}levels/{level_name}").json()

async def setup(bot):
  await bot.add_cog(RewardStat(bot))