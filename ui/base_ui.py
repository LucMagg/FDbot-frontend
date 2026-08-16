import discord
from dataclasses import dataclass, field
from typing import Optional
from services.discord_handler.discord_handler import DiscordHandler


@dataclass(slots=True)
class BaseUiData:
  channel: Optional[discord.TextChannel] = None
  interaction: Optional[discord.Interaction] = None
  previous_interaction: Optional[discord.Interaction] = None
  message: Optional[discord.Message] = None
  previous_message: Optional[discord.Message] = None
  
  discord_handler: "DiscordHandler" = field(init=False)
  langcode: str = field(init=False)

  ephemeral: bool = False
  delete_previous: bool = True
  max_attempts: int = 3
  base_backoff: float = 0.5

  wait_message: bool = False
  more_response: str = ''
  generic_error_message: bool = False
  session_already_running: bool = False
  response: Optional[dict] = None
  followup_content: Optional[list[str]] = None

  content: Optional[str] = None
  view: Optional[discord.ui.View] = None

  title: Optional[str] = None
  modal: Optional[discord.ui.Modal] = None
  files: list[discord.File] = field(default_factory=list)
  timeout_message: bool = False
  timeout: Optional[int] = 180

  # loop fields
  bot: Optional[discord.Client] = None  # pour from_channel, LoopUi
  pin: bool = False
  unpin: bool = False
  current_page: int = 0
  rankings: list[discord.Embed] = field(default_factory=list)
  is_previous_button_disabled: bool = False
  is_next_button_disabled: bool = False
  labels: dict = field(default_factory=dict)

  def __post_init__(self):
    b = self.interaction.client if self.interaction else self.bot
    if b is None:
      raise ValueError('[UI] Error : interaction or channel is required')
    self.discord_handler = DiscordHandler(b)
    try:
      self.langcode = b.language.set_language(interaction=self.interaction) if self.interaction else b.language.set_language(channel_id=self.channel.id) if self.channel else 'en'
    except Exception as e:
      b.logger.log_only('info', f'[UI] Error while setting langcode : {e} -> fallback to English')
      self.langcode = 'en'

  async def send(self):
    if self.interaction:
      result = await self.discord_handler.send(self)
    else:
      result = await self.discord_handler.send_from_channel(self)
    await self.set_message(result)
    if self.message and self.pin:
      await self.message.pin()
  
  async def set_interaction(self, interaction: discord.Interaction):
    self.previous_interaction = self.interaction
    self.interaction = interaction

  async def set_message(self, message: discord.Message):
    if message is None:
      return
    if not isinstance(message, discord.Message):
      return
    self.previous_message = self.message
    self.message = message

  def set_channel(self, channel_id):
    b = self.interaction.client if self.interaction else self.bot
    self.channel = b.get_channel(channel_id)
    self.langcode = b.language.set_language(channel_id=channel_id)
  
  async def clear(self):
    await self._clear_view()
    await self._clear_modal()
    await self._clear_embed()

  async def _clear_embed(self):
    if self.response or self.wait_message:
      if self.bot:
        self.bot.logger.log_only('debug', '[UI] Clear embed')
      self.wait_message = False
      self.more_response = ''
      self.generic_error_message = False
      self.response = None
      self.files = []

  async def _clear_view(self):
    if self.view:
      if self.bot:
        self.bot.logger.log_only('debug', '[UI] Clear view')
      self.view.clear_items()
      self.view.stop()
      self.content = None
      self.view = None
      self.files = []
      self.timeout_message = False

  async def _clear_modal(self):
    if self.modal:
      if self.bot:
        self.bot.logger.log_only('debug', '[UI] Clear modal')
      self.modal.stop()
      self.title = None
      self.modal = None
      self.timeout_message = False

  @classmethod
  def from_channel(cls, channel: discord.TextChannel, bot) -> "BaseUiData":
    instance = cls.__new__(cls)
    instance.channel = channel
    instance.interaction = None
    instance.previous_interaction = None
    instance.message = None
    instance.previous_message = None
    instance.ephemeral = False
    instance.delete_previous = True
    instance.max_attempts = 3
    instance.base_backoff = 0.5
    instance.wait_message = False
    instance.more_response = ''
    instance.generic_error_message = False
    instance.session_already_running = False
    instance.response = None
    instance.followup_content = None
    instance.content = None
    instance.view = None
    instance.title = None
    instance.modal = None
    instance.files = []
    instance.timeout_message = False
    instance.timeout = 20
    instance.discord_handler = DiscordHandler(bot)
    instance.langcode = bot.language.set_language(channel_id=channel.id)
    instance.bot = bot
    instance.pin = False
    instance.unpin = False
    instance.current_page = 0
    instance.rankings = []
    instance.is_previous_button_disabled = False
    instance.is_next_button_disabled = False
    instance.labels = {}
    return instance