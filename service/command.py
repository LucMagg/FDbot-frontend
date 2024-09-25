import typing
from discord import app_commands
from discord.app_commands import Choice


class CommandService:

  @staticmethod
  def init_command(command, command_data):
    if command_data:
      command.name = command_data['name']
      command.description = command_data['description']
      for param in command_data['options']:
        command._params[param['name']].description = param['description']
        command._params[param['name']].required = param['required']
        if 'choices' in param.keys():
          command._params[param['name']].choices = [Choice(name=p['name'], value=p['value']) for p in param['choices']]

  @staticmethod
  def set_choices(collection):
    choices = sorted([app_commands.Choice(name=c['name'], value=c['name_slug'] if 'name_slug' in c.keys() else c['name']) for c in collection], key=lambda c:c.name)
    return choices

  async def return_autocompletion(self, collection: list, current: str) -> typing.List[app_commands.Choice[str]]:
    choices = self.set_choices(collection)
    first_25_choices = [c for c in choices if current.lower() in c.name.lower()][:25]
    return first_25_choices