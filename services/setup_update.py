from typing import Optional

class SetupUpdateService:
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.commands = bot.static_data.commands

  async def command_setup_updater(self, command_types: list[str] = [], update_all_commands: bool = False):
    list_of_commands_to_update = ', '.join([c.get('name') for c in self.commands if self.check_setup_type(c.get('setup_type', ''), command_types)])
    print(list_of_commands_to_update)
    self.logger.log('debug', f'[UPDATE COMMANDS] {list_of_commands_to_update}')

    for c in self.commands:
      if self.check_setup_type(c.get('setup_type', ''), command_types) or (c.get('to_update') and update_all_commands):
        command_location = f'commands.{c.get('name')}'
        await self.bot.setup_command(command_location)

  def check_setup_type(self, setup_type: Optional[str], types_to_check: str) -> bool:
    if setup_type is None:
      return False
    for t in types_to_check:
      if t in setup_type.split('/'):
        return True
    return False