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
        command._params[param['name']].choices = [Choice(name=p['name'], value=p['value']) for p in param['choices']]