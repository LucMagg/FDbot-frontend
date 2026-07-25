from __future__ import annotations
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
  from ui.base_ui import BaseUiData


class PayloadBuilder:
  max_description_length = 4096
  max_embed_length = 6000
  max_field_name_length = 256
  max_field_value_length = 1024
  max_fields_count = 25

  def __init__(self, message, logger):
      self.message = message
      self.logger = logger

  # Entry point : build embed from data
  def build(self, data: BaseUiData) -> dict:
    embed = self._resolve_embed(data)
    if embed:
      embed.set_footer(text=self.message.get_message('footer').get(data.langcode).get('ok'))
    return {
      'content': data.content,
      'embed': embed,
      'view': data.view,
      'files': data.files if data.files else [],
    }

  # Resolve embed depending on data
  def _resolve_embed(self, data: BaseUiData) -> discord.Embed | None:
    if data.wait_message:
      return self._build_wait_embed(data)
    if data.timeout_message and data.timeout:
      return self._build_timeout_embed(data)
    if data.generic_error_message:
      return self.build_generic_error(data)
    if data.session_already_running:
      return self._build_session_error_embed(data)
    if data.response:
      return self._build_response_embed(data.response, data.langcode, data.files)
    return None

  # Embed helpers
  #    Wait message
  def _build_wait_embed(self, data: BaseUiData) -> discord.Embed:
    wait_message = self.message.get_message(whichone='wait')
    msg = wait_message.get(data.langcode)
    self.logger.log_only('debug', f'[IH] Building wait embed')
    return discord.Embed(
      description=f'## {msg.get('title')} ##\n{msg.get('description')}{data.more_response}',
      color=self._color(wait_message.get('color')),
    )

  #    Timeout message
  def _build_timeout_embed(self, data: BaseUiData) -> discord.Embed:
    error_msg = self.message.get_message(whichone='error')
    timeout_message = error_msg.get(data.langcode).get('timeout')
    inactivity = self._convert_seconds(data.timeout, timeout_message)
    self.logger.log_only('debug', f'[IH] Building timeout embed')
    return discord.Embed(
      description=f'## {timeout_message.get('title')} ## \n{timeout_message.get('cancel')} {inactivity}',
      color=self._color(error_msg.get('color')),
    )

  #    Session error message
  def _build_session_error_embed(self, data: BaseUiData) -> discord.Embed:
    session_message = self.message.get_message(whichone='error').get(data.langcode)
    self.logger.log_only('debug', f'[IH] Building session error embed')
    return discord.Embed(
      description=f'## {session_message.get('title')} ## \n{session_message.get('session')}',
      color=self._color(self.message.get_message(whichone='error').get('color')),
    )

  #    Generic error message
  def build_generic_error(self, data: BaseUiData) -> discord.Embed:
    error_message = self.message.get_message('error')
    return discord.Embed(
      description=f'## {error_message.get(data.langcode).get('title')} ##\n{error_message.get(data.langcode).get('generic')}',
      color=self._color(error_message.get('color')),
    )

  #    Builder (checks embed length)
  def _build_response_embed(self, response: dict, langcode: str, files: list[discord.File]) -> discord.Embed:
    footer_ok = self.message.get_message('footer').get(langcode).get('ok')
    footer_too_long = self.message.get_message('footer').get(langcode).get('too_long')
    description = self._truncate_description(response.get('description', ''), footer_ok, footer_too_long)
    fields = self._validate_fields(response.get('fields', []))
    total = len(description) + sum(len(f.get('name', '')) + len(f.get('value', '')) for f in fields)
    if total > self.max_embed_length:
      self.logger.log_only('warning', f'[IH] Embed over max limit ({total} chars)')
    embed = discord.Embed(description=description, color=self._color(response.get('color')))
    for field in fields:
      embed.add_field(name=field.get('name', '\u200b'), value=field.get('value', '\u200b'), inline=field.get('inline', False))
    if 'image' in response:
      if files and len(files) == 1:
        embed.set_image(url=f'attachment://{files[0].filename}')
      elif not files:
        embed.set_image(url=response.get('image'))
    if 'thumbnail' in response:
      embed.set_thumbnail(url=response.get('thumbnail'))
    self.logger.log_only('debug', '[IH] Response embed built')
    return embed

  # Truncate description (if > max_description_length)
  def _truncate_description(self, description: str, footer_ok: str, footer_too_long: str) -> str:
    if len(description) + len(footer_ok) > self.max_description_length:
      max_length = self.max_description_length - len(footer_ok) - len(footer_too_long)
      return description[:max_length] + footer_too_long
    return description

  # Validate fields (checks fields count & lengths)
  def _validate_fields(self, fields: list) -> list:
    if len(fields) > self.max_fields_count:
      self.logger.log_only('warning', f'[IH] Too many fields ({len(fields)}), truncated to {self.max_fields_count}')
      fields = fields[:self.max_fields_count]
    validated = []
    for field in fields:
      name = field.get('name', '\u200b')
      value = field.get('value', '\u200b')
      if len(name) > self.max_field_name_length:
        self.logger.log_only('warning', '[IH] Field name too long, truncated')
        name = name[:self.max_field_name_length]
      if len(value) > self.max_field_value_length:
        self.logger.log_only('warning', '[IH] Field value too long, truncated')
        value = value[:self.max_field_value_length]
      validated.append({**field, 'name': name, 'value': value})
    return validated

  # Discord color helper
  def _color(self, color: str) -> discord.Color:
    match str.lower(color):
      case 'default':
        return discord.Color.default()
      case 'red':
        return discord.Color.red()
      case 'green':
        return discord.Color.green()
      case 'blue':
        return discord.Color.blue()
      case 'light':
        return discord.Color.gold()
      case 'dark':
        return discord.Color.magenta()

  # Converts seconds into minutes/seconds (for timeout message)
  def _convert_seconds(self, seconds: int, timeout_message: dict) -> str:
    to_return = []
    minutes = seconds // 60
    if minutes > 0:
      seconds = seconds % 60
      to_return.append(f'{minutes} {timeout_message.get(f'minute{'s' if minutes > 1 else ''}')}')
    if seconds > 0:
      to_return.append(f'{seconds} {timeout_message.get(f'second{'s' if seconds > 1 else ''}')}')
    return timeout_message.get('and').join(to_return)