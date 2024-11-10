import typing
from discord import app_commands
from discord.app_commands import Choice


class CommandService:

  @staticmethod
  def init_command(command, command_data, no_choices=False):
    if command_data:
      command.name = command_data['name']
      command.description = command_data['description']
      for param in command_data['options']:
        command._params[param['name']].description = param['description']
        command._params[param['name']].required = param['required']
        if 'choices' in param.keys() and not no_choices:
          command._params[param['name']].choices = [Choice(name=p['name'], value=p['value']) for p in param['choices']]

  @staticmethod
  def set_choices(collection):
    choices = sorted([app_commands.Choice(name=c['name'], value=c['name_slug'] if 'name_slug' in c.keys() else c['name']) for c in collection], key=lambda c:c.name)
    return choices
  
  @staticmethod
  def set_choices_by_rewards(collection):
    def sort_function(document):
      return sum([reward.get('total_appearances', 0) for reward in document.get('rewards')])
    
    sorted_collection = sorted(collection, key=lambda c: (sort_function(c), c.get('name')), reverse=True)
    choices = [app_commands.Choice(name=c['name'], value=c['name']) for c in sorted_collection]

    return choices

  @staticmethod
  async def return_autocompletion(choices: list, current: str) -> typing.List[app_commands.Choice[str]]:
    first_25_choices = [c for c in choices if current.lower() in c.name.lower()][:25]
    return first_25_choices