import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from sessions.level import LevelSession
from utils.session_decorator import session_command


class Level(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.choices = None
    self.reward_types = None
    self.all_languages_levels = None

  async def level_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return await self.bot.command.return_autocompletion(self.choices.get('en'), current.strip())

  @app_commands.autocomplete(name_in_english=level_autocomplete)
  @app_commands.command(name='level')
  @session_command(command_name='level', oneshot=False)
  async def level_app_command(self, interaction: discord.Interaction, name_in_english: str, standard_energy_cost: Optional[int] = None, coop_energy_cost: Optional[int] = None):
    self.logger.log('debug', f'[LEVEL] name_in_english : {name_in_english} | standard_energy_cost : {standard_energy_cost} | coop_energy_cost : {coop_energy_cost}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'name_in_english': name_in_english,
      'standard_energy_cost': standard_energy_cost,
      'coop_energy_cost': coop_energy_cost      
    }
    session = LevelSession(session_data)
    await session.start()

  def _build_reward_tree(self, raw_rewards: list[dict]) -> list[dict]:
    result = []
    for reward in raw_rewards:
      reward_copy = reward.copy()
      reward_copy['rid'] = reward['_id']
      result_groups = []
      for gi, group in enumerate(reward.get('choices', [])):
        group_copy = group.copy()
        group_copy['gid'] = f'{reward['_id']}:g{gi}'
        result_choices = []
        for ci, choice in enumerate(group.get('choices', [])):
          choice_copy = choice.copy()
          choice_copy['cid'] = f'{reward['_id']}:g{gi}:c{ci}'
          result_choices.append(choice_copy)
        group_copy['choices'] = result_choices
        result_groups.append(group_copy)
      reward_copy['choices'] = result_groups
      result.append(reward_copy)
    return result
      
  async def setup(self):
    self.all_languages_levels = await self.bot.command.set_choices(['levels'])
    self.choices = {'en': [app_commands.Choice(name=c.name, value=c.name) for c in self.all_languages_levels.get('en')]}
    self.reward_types = self._build_reward_tree(await self.bot.back_requests.call('getAllRewardTypes'))

async def setup(bot):
  await bot.add_cog(Level(bot))