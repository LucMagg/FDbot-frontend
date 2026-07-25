class TrapService:
  def __init__(self, bot):
    self.bot = bot
  
  async def __post_init__(self):
    self.bot.trap_roles = await self.bot.back_requests.call('getAllTrapRoles')