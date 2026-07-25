import asyncio
import time
import discord
from typing import Dict, Any, Optional, Callable
from utils.misc_utils import nick
from ui.base_ui import BaseUiData


class SessionManager:
  def __init__(self, bot, ttl_seconds: int = 600, rate_limit_seconds: int = 1):
    self.bot = bot
    self.logger = bot.logger
    self.sessions: Dict[int, Dict[str, Any]] = {}
    self.locks: Dict[int, asyncio.Lock] = {}
    self.ttl_seconds = ttl_seconds
    self.rate_limit_seconds = rate_limit_seconds

  def _uid(self, interaction: discord.Interaction) -> int:
    return interaction.user.id

  def get_lock(self, interaction: discord.Interaction) -> asyncio.Lock:
    user_id = self._uid(interaction)
    if user_id not in self.locks:
      self.logger.log_only('debug', f'[SESSION] Creating lock for {nick(interaction)}')
      self.locks[user_id] = asyncio.Lock()
    return self.locks[user_id]

  def create(self, interaction: discord.Interaction):
    self.sessions[self._uid(interaction)] = {
      'created_at': time.time(),
      'last_call': 0,
      'nick': nick(interaction)
    }
    self.logger.log_only('debug', f'[SESSION] Created session for {nick(interaction)}')

  def get(self, interaction: discord.Interaction) -> Optional[Dict[str, Any]]:
    return self.sessions.get(self._uid(interaction))

  def delete(self, interaction: discord.Interaction):
    user_id = self._uid(interaction)
    session = self.sessions.pop(user_id, None)
    if session:
      self.logger.log_only('debug', f'[SESSION] Deleted session for {session['nick']}')

  async def cleanup_loop(self):
    self.logger.log_only('info', '[SESSION] Cleanup loop started')
    while True:
      now = time.time()
      for user_id, session in list(self.sessions.items()):
        if now - session['created_at'] > self.ttl_seconds:
          self.logger.log_only('debug', f'[SESSION] Session expired for {session['nick']}')
          self.sessions.pop(user_id, None)
          self.locks.pop(user_id, None)
      await asyncio.sleep(30)

  async def run(self, interaction: discord.Interaction, command_name: str, callback: Callable, *, oneshot: bool = True):
    session = self.get(interaction)
    if session:
      self.logger.log_only('warning', f'[SESSION] Active session for {nick(interaction)}')
      try:
        ui = BaseUiData(interaction=interaction)
        ui.session_already_running = True
        await ui.send()
      except Exception:
        pass
      return
    lock = self.get_lock(interaction)
    if lock.locked():
      self.logger.log_only('warning', f'[SESSION] Lock already held for {nick(interaction)}')
      return
    async with lock:
      session = self.get(interaction)
      if session:
        self.logger.log_only('warning', f'[SESSION] Race condition avoided for {nick(interaction)}')
        return
      self.create(interaction)
      session = self.get(interaction)
      now = time.time()
      if now - session['last_call'] < self.rate_limit_seconds:
        self.logger.log_only('warning', f'[SESSION] Rate limit for {session['nick']}')
        return
      session['last_call'] = now
      try:
        self.logger.command_log(command_name, interaction)
        result = await callback()
        return result
      except Exception as e:
        self.logger.log_only('error', f'[SESSION] Error in {command_name}: {e}')
      finally:
        if oneshot:
          self.logger.ok_log(command_name, interaction)
          self.delete(interaction)