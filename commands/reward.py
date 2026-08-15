import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.session_decorator import session_command
from sessions.reward_add import RewardAddSession
from sessions.reward_show import RewardShowSession


class Reward(commands.Cog):
  reward = app_commands.Group(name='reward', description='...')

  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.level_choices = None

  async def level_choices_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    langcode = self.bot.language.set_language(interaction=interaction)
    return await self.bot.command.return_autocompletion(self.level_choices[langcode], current.strip())

  @app_commands.autocomplete(level=level_choices_autocomplete)
  @reward.command(name='add')
  @session_command(command_name='reward add', oneshot=False)
  async def rewardadd_app_command(self, interaction: discord.Interaction, level: str):
    self.logger.log_only('debug', f'[REWARD ADD] level : {level} | interaction : {interaction.id}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'level': level
    }
    session = RewardAddSession(session_data)
    await session.start()

  @app_commands.autocomplete(level=level_choices_autocomplete)
  @reward.command(name='show')
  @session_command(command_name='reward show')
  async def rewardshow_app_command(self, interaction: discord.Interaction, level: str):
    self.logger.log_only('debug', f'[REWARD SHOW] level : {level} | interaction : {interaction.id}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'level': level
    }
    session = RewardShowSession(session_data)
    await session.start()

  async def setup(self, level_list: Optional[list[dict]] = None):
    if level_list is None:
      self.level_choices = await self.bot.command.set_choices(['sorted levels'])
    else:
      self.level_choices = level_list

async def setup(bot):
  await bot.add_cog(Reward(bot))