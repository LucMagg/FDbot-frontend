import discord
from dataclasses import dataclass, field
from typing import Optional
from services.discord_handler.discord_handler import DiscordHandler


@dataclass(slots=True)
class LoopUi:
  bot: discord.Client
  discord_handler: "DiscordHandler" = field(init=False)
  langcode: str = field(default_factory=str)

  channel: Optional[discord.TextChannel] = None
  interaction: Optional[discord.Interaction] = None
  previous_interaction: Optional[discord.Interaction] = None
  message: Optional[discord.Message] = None
  previous_message: Optional[discord.Message] = None
  
  content: Optional[str] = ''
  response: Optional[discord.Embed] = None
  view: Optional[discord.ui.View] = None

  delete_previous: bool = True
  max_attempts: int = 3
  base_backoff: float = 0.5

  pin: bool = False
  unpin: bool = False

  current_page: int = field(default_factory=int)
  rankings: list[discord.Embed] = field(default_factory=list)
  is_previous_button_disabled: bool = False
  is_next_button_disabled: bool = False
  labels: dict = field(default_factory=dict)

  def __post_init__(self):
    self.discord_handler = DiscordHandler(self.bot)

  async def send(self):
    result = await self.discord_handler.send_from_loop(self)
    await self.set_message(result)
    if self.message and self.pin:
      await self.message.pin()

  async def set_interaction(self, interaction: discord.Interaction):
    self.previous_interaction = self.interaction
    self.interaction = interaction

  def set_channel(self, channel_id):
    self.channel = self.bot.get_channel(channel_id)
    self.langcode = self.bot.language.set_language(channel_id=channel_id)
  
  async def set_message(self, message: discord.Message):
    if message is None:
      return
    if not isinstance(message, discord.Message):
      return
    self.previous_message = self.message
    self.message = message
  
  async def clear(self):
    await self._clear_view()
    await self._clear_embed()

  async def _clear_embed(self):
    if self.response:
      self.response = None

  async def _clear_view(self):
    if self.view:
      self.view.clear_items()
      self.view.stop()
      self.content = ''
      self.view = None