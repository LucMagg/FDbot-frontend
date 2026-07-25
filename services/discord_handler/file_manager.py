import discord, io
 
class FileManager:
 
  def __init__(self):
    self.last_message_with_files_ids: list[int] = []
    self.had_files: bool = False

  # Get last message with files id after send successful
  def notify_sent(self, files: list[discord.File], message):
    if files and hasattr(message, 'id'):
      self.last_message_with_files_ids = [message.id]
      self.had_files = True

  # Delete previous messages with files if new one doesn't have any
  async def cleanup_if_needed(self, interaction: discord.Interaction, new_files: list[discord.File]):
    if not (self.had_files and not new_files and self.last_message_with_files_ids):
      return
    for msg_id in self.last_message_with_files_ids:
      try:
        msg = await interaction.channel.fetch_message(msg_id)
        await msg.delete()
      except Exception:
        pass
    self.last_message_with_files_ids = []
    self.had_files = False

  # Inject files depending strategy
  def inject(self, kwargs: dict, strategy, files: list[discord.File], send_strategies: set):
    if not files:
      return
    fresh = []
    for f in files:
      path = getattr(f, '_original_path', None) or getattr(f.fp, 'name', None)
      is_bytes_io = isinstance(getattr(f, 'fp', None), io.BytesIO)
      if path and not is_bytes_io:
        fresh.append(discord.File(path, filename=f.filename))
      else:
        self.rewind([f])
        fresh.append(f)
    if strategy in send_strategies:
      kwargs['files'] = fresh
    else:
      kwargs['attachments'] = fresh

  @staticmethod
  # Set file buffer to 0
  def rewind(files: list[discord.File]):
    for f in files:
      if hasattr(f, 'fp') and hasattr(f.fp, 'seek'):
        f.fp.seek(0)