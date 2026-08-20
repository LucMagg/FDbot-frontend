from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
import discord
from discord.errors import HTTPException, InteractionResponded

from services.discord_handler.file_manager import FileManager

if TYPE_CHECKING:
  from ui.base_ui import BaseUiData
  from services.loop.loop_ui import LoopUi


class StrategyRunner:
  def __init__(self, logger, file_manager: FileManager):
      self.logger = logger
      self.file_manager = file_manager

  # Entry point
  async def run(self, data: BaseUiData|LoopUi, payload: dict):
    if data.interaction:
      await self._ensure_deferred(data.interaction)
    if data.interaction:
      await self.file_manager.cleanup_if_needed(data.interaction, payload.get('files', []))
    result = await self._try_strategies(data, payload)
    if result and data.delete_previous and (data.previous_interaction or data.previous_message):
      await self._safe_delete_previous(data, result)
    return result

  # Try strategies
  async def _try_strategies(self, data: BaseUiData|LoopUi, payload: dict):
    strategies, message_strategies, send_strategies = self._build_strategies(data)
    base_kwargs = self._base_kwargs(payload)
    for strategy in strategies:
      for attempt in range(data.max_attempts):
        try:
          strategy_kwargs = self._prepare_kwargs(strategy, message_strategies, base_kwargs, payload, send_strategies)
          result = await strategy(**strategy_kwargs)
          if data.interaction:
            log_id = data.interaction.id
          elif data.message:
            log_id = data.message.id
          else:
            log_id = result.id
          self.logger.log('debug', f'[IH] Response sent | strategy={strategy.__name__} | id={log_id}')
          self.file_manager.notify_sent(payload.get('files', []), result)
          return result
        except HTTPException as e:
          if e.status == 404:
            self.logger.log('warning', f'[IH] Strategy {strategy.__name__} got 404 → skipping')
            break
          wait = getattr(e, 'retry_after', None) or (data.base_backoff * (2 ** attempt))
          if e.status == 429:
            self.logger.log('warning', f'[IH] Rate limited. Sleeping {wait}s')
          else:
            self.logger.log('warning', f'[IH] Strategy {strategy.__name__} failed (attempt {attempt + 1}): {e}')
          await asyncio.sleep(wait)
        except InteractionResponded:
          self.logger.log('warning', f'[IH] Strategy {strategy.__name__} already responded → skipping')
          break
        except Exception as e:
          self.logger.log('warning', f'[IH] Strategy {strategy.__name__} failed (attempt {attempt + 1}): {e}')
          await asyncio.sleep(data.base_backoff * (2 ** attempt))
      else:
        self.logger.log('warning', f'[IH] Strategy {strategy.__name__} exhausted all attempts')
    prev_id = data.previous_interaction.id if data.previous_interaction else None
    self.logger.log('error', f'[IH] All strategies failed | interaction={data.interaction.id} | previous={prev_id}')
    return None

  # Kwargs builders
  #    cleanup kwargs
  def _base_kwargs(self, payload: dict) -> dict:
    return {k: v for k, v in {
      'content': payload.get('content'),
      'embed': payload.get('embed'),
      'view': payload.get('view'),
    }.items() if v is not None}

  #    Prepare kwargs (depending the strategy)
  def _prepare_kwargs(self, strategy, message_strategies: set, base_kwargs: dict, payload: dict, send_strategies: set) -> dict:
    kwargs = {**base_kwargs}
    if strategy in message_strategies:
      if 'view' not in kwargs:
        kwargs['view'] = None
        kwargs['content'] = None
      if 'embed' not in kwargs:
        kwargs['embed'] = None
    else:
      kwargs.setdefault('view', discord.utils.MISSING)
    self.file_manager.inject(kwargs, strategy, payload.get('files', []), send_strategies)
    return kwargs

  # Strategies builder
  def _build_strategies(self, data: BaseUiData|LoopUi) -> tuple[list, set, set]:
    strategies = []
    message_strategies = set()
    send_strategies = set()
    # 1: message edition
    for msg in [data.message, data.previous_message]:
      if msg:
        strategies.append(msg.edit)
        message_strategies.add(msg.edit)
        break
    # 2: interaction response
    if data.interaction and data.interaction.response.is_done():
      strategies.append(data.interaction.edit_original_response)
      strategies.append(data.interaction.response.edit_message)
    elif data.interaction:
      strategies.append(data.interaction.response.edit_message)
      strategies.append(data.interaction.edit_original_response)
    # 3: previous interaction followup
    if data.previous_interaction:
      strategies.append(data.previous_interaction.followup.send)
      send_strategies.add(data.previous_interaction.followup.send)
    # 4: basic send
    if data.interaction:
      strategies.append(data.interaction.channel.send)
      send_strategies.add(data.interaction.channel.send)
    if data.channel:
      strategies.append(data.channel.send)
      send_strategies.add(data.channel.send)
    return strategies, message_strategies, send_strategies

  # Defer interaction
  async def _ensure_deferred(self, interaction: discord.Interaction) -> None:
    try:
      if not interaction.response.is_done():
        await interaction.response.defer()
    except InteractionResponded:
      self.logger.log('warning', f'[IH] Defer: {interaction.id} already responded')
    except HTTPException as e:
      self.logger.log('warning', f'[IH] Defer HTTPException {e.status}: {e}')
    except Exception as e:
      self.logger.log('warning', f'[IH] Defer unknown error: {e}')

  # Delete previous interaction/message if exists
  async def _safe_delete_previous(self, data: BaseUiData|LoopUi, result: discord.Message|None) -> None:
    if data.previous_message and isinstance(result, discord.Message) and result.id == data.previous_message.id:
      return
    if data.previous_interaction:
      try:
        msg = await data.previous_interaction.original_response()
        if msg.pinned():
          await msg.unpin()
          self.logger.log('debug', f'[IH] Previous interaction unpinned: {msg.id}')
        await msg.delete()
        self.logger.log('debug', f'[IH] Previous interaction deleted: {msg.id}')
      except Exception:
        pass
    if data.previous_message:
      try:
        if data.previous_message.pinned:
          await data.previous_message.unpin()
          self.logger.log('debug', f'[IH] Previous message unpinned: {data.previous_message.id}')
        await data.previous_message.delete()
        self.logger.log('debug', f'[IH] Previous message deleted: {data.previous_message.id}')
      except Exception:
        pass