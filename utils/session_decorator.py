from functools import wraps

def session_command(command_name: str, *, oneshot: bool = True):
  def decorator(func):
    @wraps(func)
    async def wrapper(self, interaction, *args, **kwargs):
      async def callback():
        return await func(self, interaction, *args, **kwargs)
      return await self.bot.session_manager.run(interaction=interaction, command_name=command_name, callback=callback, oneshot=oneshot)
    return wrapper
  return decorator