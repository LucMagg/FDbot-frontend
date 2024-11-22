import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

from service.interaction_handler import InteractionHandler


class TestCommand(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.interaction_handler = InteractionHandler(self.bot)


  @app_commands.command(name='testcommand')
  async def testcommand_app_command(self, interaction: discord.Interaction):
    self.logger.command_log('testcommand', interaction)
    await self.interaction_handler.handle_response(interaction=interaction, wait_msg=True)
    date = (datetime.now() - timedelta(days=0)).isoformat()
    print(date)
    message = await self.bot.spire_ranking_service.display_scores(date=date, interaction=interaction)
    
    message.pin()
    self.logger.ok_log('testcommand')
  
async def setup(bot):
  await bot.add_cog(TestCommand(bot))