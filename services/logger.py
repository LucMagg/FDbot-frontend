import os
import logging
import discord
from logging.handlers import RotatingFileHandler
from utils.str_utils import str_now

class Logger:
  def __init__(self, log_file):
    self.setup_logger(log_file)

  def setup_logger(self, log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    self.logger = logging.getLogger('discord_bot')
    self.logger.setLevel(logging.DEBUG)

    file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5, encoding='utf-8')
    
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)

    if not self.logger.handlers:
      self.logger.addHandler(file_handler)

  def command_log(self, cmd: str, interaction: discord.Interaction):
    message = f'[{str_now()}] [{cmd.upper()}] Command entered by [{interaction.user}] in channel [{interaction.channel}] of server [{interaction.guild.name}]'
    print(message)
    self.logger.info(message)

  def command_fail(self, cmd: str, interaction: discord.Interaction):
    message = f'[{str_now()}] [{cmd.upper()}] [{interaction.user}] session already ongoing | failed to start command [{cmd}]'
    print(message)
    self.logger.info(message)

  def ok_log(self, cmd: str, interaction: discord.Interaction):
    message = f'[{str_now()}] [{cmd.upper()}] Command success for [{interaction.user}]'
    print(message)
    self.logger.info(message)

  def nok_log(self, cmd: str, interaction: discord.Interaction):
    message = f'[{str_now()}] [{cmd.upper()}] Command error for [{interaction.user}]'
    print(message)
    self.logger.info(message)

  def timeout_log(self, cmd: str, interaction: discord.Interaction):
    message = f'[{str_now()}] [{cmd.upper()}] Command timeout for [{interaction.user}]'
    print(message)
    self.logger.info(message)

  def error_log(self, msg: str):
    message = f'[{str_now()}] [ERROR] {msg}'
    print(message)
    self.logger.error(message)

  def bot_log(self, msg: str):
    message = f'[{str_now()}] {msg}'
    print(message)
    self.logger.info(message)

  def log_only(self, level: str, msg: str):
    message = f'[{str_now()}] {msg}'
    match level:
      case 'debug':
        self.logger.debug(message)
      case 'info':
        self.logger.info(message)
      case 'warning':
        self.logger.warning(message)
      case 'error':
        self.logger.error(message)
      case _:
        self.logger.info(message)