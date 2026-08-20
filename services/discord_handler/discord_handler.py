from __future__ import annotations
from typing import TYPE_CHECKING

from services.discord_handler.file_manager import FileManager
from services.discord_handler.payload_builder import PayloadBuilder
from services.discord_handler.strategy_runner import StrategyRunner

from utils.misc_utils import nick

if TYPE_CHECKING:
  from ui.base_ui import BaseUiData
  from services.loop.loop_ui import LoopUi


class DiscordHandler:
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.message = bot.message

    self.file_manager = FileManager()
    self.payload_builder = PayloadBuilder(self.message, self.logger)
    self.strategy_runner = StrategyRunner(self.logger, self.file_manager)

  # Entry point to handle discord interaction/message
  async def send(self, data: BaseUiData):
    self.logger.log('debug', f'[IH] Interaction {data.interaction.id} | User {data.interaction.user.id} [{nick(data.interaction)}]')
    payload = {}
    try:
      if data.modal:
        self.logger.log('debug', f'[IH] Sending modal for interaction {data.interaction.id}')
        return await self._send_modal(data)
      payload = self.payload_builder.build(data)
      self.logger.log('debug',(
        f'[IH] Payload built | interaction={data.interaction.id} | content={bool(payload.get('content'))}|embed={bool(payload.get('embed'))}'
        f'|view={bool(payload.get('view'))}|files={len(payload.get('files', []))}'
      ))
      result = await self.strategy_runner.run(data, payload)
      if result is None:
        data.send_failed = True
        result = await self._hard_fallback(data)
      if result:
        self._clear_oneshot_fields(data)
        if data.followup_content:
          for content in data.followup_content:
            await data.interaction.channel.send(content=content)
          data.followup_content = None
      return result
    except Exception as e:
      self.logger.log('error', f'[IH] Interaction {data.interaction.id} | {e}')
      data.send_failed = True
      fallback_result = await self._hard_fallback(data)
      if fallback_result:
        self._clear_oneshot_fields(data)
      return fallback_result
    
  # Entry point to handle loop messages
  async def send_from_loop(self, data: LoopUi):
    self.logger.log('debug', f'[IH] Channel {data.channel.id}')
    payload = {'embed': data.response, 'view': data.view}
    try:
      result = await self.strategy_runner.run(data, payload)
      if result is None:
        data.send_failed = True
        result = await self._hard_fallback(data)
      return result
    except Exception as e:
      self.logger.log('error', f'[IH] Channel {data.channel.id} | {e}')
      data.send_failed = True
      fallback_result = await self._hard_fallback(data)
      return fallback_result
    
  # Entry point to handle messages from channel (no interaction)
  async def send_from_channel(self, data: BaseUiData):
    self.logger.log('debug', f'[IH] Channel {data.channel.id}')
    payload = self.payload_builder.build(data)
    try:
      result = await data.channel.send(
        **{k: v for k, v in {
          'content': payload.get('content'),
          'embed': payload.get('embed'),
          'view': payload.get('view'),
          'files': payload.get('files')
        }.items() if v is not None}
      )
      self.logger.log('debug', f'[IH] Result: {result}')
      if result:
        if data.delete_previous and data.previous_message:
          await self.strategy_runner._safe_delete_previous(data, result)
        self._clear_oneshot_fields(data)
      return result
    except Exception as e:
      data.send_failed = True
      self.logger.log('error', f'[IH] Channel {data.channel.id} | {e}')
      return
  
  # Modal sender
  async def _send_modal(self, data: BaseUiData):
    try:
      return await data.interaction.response.send_modal(data.modal)
    except Exception:
      self.logger.log('warning', f'[IH] Modal: interaction {data.interaction.id} already responded')
      if data.previous_interaction:
        try:
          return await data.previous_interaction.send_modal(data.modal)
        except Exception:
          self.logger.log('error', f'[IH] Modal fallback failed | interaction={data.interaction.id} | previous={data.previous_interaction.id}')
          data.send_failed = True
          return await data.previous_interaction.followup.send(embed=self.payload_builder.build_generic_error(data))
      else:
        self.logger.log('error', f'[IH] Modal failed, no previous interaction | {data.interaction.id}')
        data.send_failed = True
        return await data.interaction.followup.send(embed=self.payload_builder.build_generic_error(data))
  
  # Fallback if all strategies failed
  async def _hard_fallback(self, data: BaseUiData):
    error_embed = self.payload_builder.build_generic_error(data)
    self.logger.log('error', '[IH] Hard fallback triggered')
    if data.previous_interaction:
      try:
        return await data.previous_interaction.followup.send(embed=error_embed)
      except Exception:
        pass
    try:
      return await data.interaction.channel.send(embed=error_embed)
    except Exception as e:
      self.logger.log('error', f'[IH] Total failure: {e}')
      return None
  
  # Clear oneshot fields
  def _clear_oneshot_fields(self, data: BaseUiData) -> None:
    data.wait_message = False
    data.more_response = ''
    data.generic_error_message = False
    data.timeout_message = False
    data.response = None