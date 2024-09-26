from utils.str_utils import str_now

class Logger:
  @staticmethod
  def command_log(cmd, interaction):
    print(f'[{str_now()}] [COMMAND] commande {cmd} entrée par {interaction.user} dans le chan {interaction.channel} du serveur {interaction.guild.name}')

  @staticmethod
  def ok_log(cmd):
    print(f'[{str_now()}] [COMMAND] commande {cmd} exécutée avec succès')