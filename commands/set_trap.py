import discord
from discord.ext import commands
from discord import app_commands

from utils.session_decorator import session_command
from sessions.set_trap import Set_trapSession

from utils.misc_utils import nick


class Set_trap(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger

  @app_commands.default_permissions(administrator=True)
  @app_commands.command(name='set_trap')
  @session_command(command_name='set_trap')
  async def settraprole_app_command(self, interaction: discord.Interaction, trap_id: str):
    self.logger.log('debug', f'[SET_TRAP] {nick(interaction)} setting trap role in channel {interaction.channel_id} : trap role id {trap_id}')
    session_data = {
      'cog': self,
      'interaction': interaction,
      'trap_id': trap_id
    }
    session = Set_trapSession(session_data)
    await session.start()
     
async def setup(bot):
  await bot.add_cog(Set_trap(bot))