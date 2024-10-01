import typing
import discord

from discord.ext import commands
from discord import app_commands

from service.command import CommandService
from service.level import LevelService
from utils.sendMessage import SendMessage

class RewardStat(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.send_message = SendMessage(self.bot)
    self.level_data = bot.level_data
    self.reward_stat_command = next((c for c in bot.static_data.commands if c['name'] == 'reward-stat'), None)
    self.gear_qualities = [g for g in bot.static_data.qualities if g['type'] == 'gear']
    self.dust_qualities = bot.static_data.dusts

    CommandService.init_command(self.reward_stat_app_command, self.reward_stat_command)

  async def level_autocompletion(self, interaction: discord.Interaction, current: str
                                 ) -> typing.List[app_commands.Choice[str]]:
    return [level for level in self.level_data.known_levels if current in level.name][:25]

  @app_commands.autocomplete(level=level_autocompletion)
  @app_commands.command(name='reward-stat')
  async def reward_stat_app_command(self, interaction: discord.Interaction, level: str):
    self.logger.command_log('reward-stat', interaction)
    if level not in [level.name for level in self.level_data.known_levels]:
      await self.send_message.error(interaction, "Ce niveau n'existe pas", "Veuillez choisir un niveau dans la liste ou contacter Prep ou Spirou.")
      self.logger.ok_log('reward-stat')
      return

    await self.send_message.post(interaction)
    response = LevelService.get_reward_response('show', interaction.guild.emojis, level, '', 0, self.gear_qualities, self.dust_qualities)
    await self.send_message.update(interaction, response)
    self.logger.ok_log('reward-stat')

async def setup(bot):
  await bot.add_cog(RewardStat(bot))