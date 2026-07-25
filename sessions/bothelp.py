from ui.base_ui import BaseUiData


class BotHelpSession:
  def __init__(self, cog_data: dict):
    self.cog = cog_data.get('cog')
    self.bot = self.cog.bot
    self.logger = self.cog.logger

    self.ui = BaseUiData(interaction=cog_data.get('interaction'))

  async def start(self):
    self.ui.wait_message = True
    await self.ui.send()
    await self.ui.clear()
    self.ui.response = self.bot.message.get_help(whichone='help', lang=self.ui.langcode)
    await self.ui.send()