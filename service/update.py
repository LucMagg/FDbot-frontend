
class UpdateService:
  def __init__(self, bot):
    self.bot = bot
    self.commands = bot.static_data.commands

  async def command_setup_updater(self, command_types: list, update_all_commands: bool):
    list_of_commands_to_update = [c for c in self.commands if self.check_setup_type(c.get('setup_type', ''), command_types)]

    heroes = None
    if any(l for l in list_of_commands_to_update if self.check_setup_type(l.get('setup_type', ''), ['hero'])) or update_all_commands:
      heroes = await self.bot.back_requests.call('getAllHeroes', False)

    pets = None
    if any(l for l in list_of_commands_to_update if self.check_setup_type(l.get('setup_type', ''), ['pet'])) or update_all_commands:
      pets = await self.bot.back_requests.call('getAllPets', False)

    levels = None
    if any(l for l in list_of_commands_to_update if self.check_setup_type(l.get('setup_type', ''), ['level'])):
      levels = await self.bot.back_requests.call('getAllLevels', False)

    for c in self.commands:
      if self.check_setup_type(c.get('setup_type', ''), command_types) or (c.get('to_update') and update_all_commands):
        command_location = f"commands.{c.get('name')}" 
        match c.get('setup_type', ''):
          case 'hero':
            await self.bot.setup_command(command_location, heroes)
          case 'hero/pet':
            if heroes is not None and pets is not None:
              await self.bot.setup_command(command_location, [heroes, pets])
            else:
              await self.bot.setup_command(command_location)
          case 'pet':
            await self.bot.setup_command(command_location, pets)
          case 'level':
            await self.bot.setup_command(command_location, levels)
          case 'replay':
            await self.bot.setup_command(command_location)
          case _:
            await self.bot.setup_command(command_location)

  def check_setup_type(self, setup_type, types_to_check):
    if setup_type is None:
      return False
    for t in types_to_check:
      if t in setup_type.split('/'):
        return True
    return False