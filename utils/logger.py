from utils.str_utils import str_now

class Logger:
  def __init__(self) -> None:
    pass

  def command_log(cmd, interaction):
    print(f'[{str_now()}] [COMMAND ] commande {cmd} entrée par {interaction.user} dans le chan {interaction.channel} du serveur {interaction.guild.name}')

  def ok_log(cmd):
    print(f'[{str_now()}] [COMMAND ] commande {cmd} exécutée avec succès')