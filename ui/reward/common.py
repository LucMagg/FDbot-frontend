from __future__ import annotations
import io
import discord
from typing import TYPE_CHECKING

from math import floor
from matplotlib import pyplot as plt
from PIL import Image
from utils.str_utils import format_float, int_to_str

if TYPE_CHECKING:
  from sessions.reward_add import RewardAddSession
  from sessions.reward_show import RewardShowSession


str_gap = '\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0'
chart_color = {
  'blue': '#3498db',
  'purple': '#9b59b6',
  'yellow': '#f1c40f',
  'red': '#e74c3c',
  'green': '#2ecc71',
  'orange': '#e67e22',
  '💰': '#c8a84b',
  'potion': {
    'fire': '#e74c3c',
    'earth': '#2ecc71',
    'sea': '#3498db',
    'light': '#f1c40f',
    'moon': '#9b59b6',
    'default': '#5865f2'
  },
  'default': '#5865F2'
}

class RewardCommon:
  def __init__(self, session: RewardAddSession|RewardShowSession):
    self.session = session
    self.rewards = self.session.state.level.get('rewards', [])
    self.reward_choices = self.session.state.level.get('reward_choices', [])
    self.total_appearances = sum(r.get('total_appearances', 0) for r in self.rewards)
    self.has_multiple_types = len(self.rewards) > 1 or len(self.reward_choices) > 1
    self.emojis = self.session.ui.interaction.guild.emojis

  # Display rewards (entry point)
  def display_rewards(self) -> str:
    try:
      if len(self.rewards) == 0:
        return self.session.return_msg.get('no reward'), None
      lines = []
      if self.has_multiple_types:
        for reward, chart_entry in zip(self.rewards, self._get_chart_data()):
          icon = chart_entry['icon']
          lines.append(self._append_with_multiple_reward_types(reward, icon, chart_entry))
      else:
        reward = self.rewards[0]
        icon = self._resolve_icon(reward)
        lines.append(self._append_with_single_reward_type(reward, icon))
      return (
        f'### {self.session.return_msg.get('list1')}{self.total_appearances}'
        f'{self.session.return_msg.get(f'list2{'S' if self.total_appearances == 1 else 'P'}')} ### \n'
        f'{''.join(lines)}'
      ), self._chart()
    except Exception as e:
      print(e)
  
  # Chart data
  def _get_chart_data(self) -> list[dict]:
    data = []
    for reward in self.rewards:
      reward_type = reward.get('type')
      quality = reward.get('quality')
      total = reward.get('total_appearances', 0)
      icon = self._resolve_icon(reward)
      color = self._get_emoji_color(self._find_icon(reward))
      base_label = self.session._translate(f'{quality} {reward_type}') if quality else self.session._translate(reward_type)
      if self.has_multiple_types:
        data.append({
          'label': self.session._translate(f'{quality} {reward_type}') if quality else self.session._translate(reward_type),
          'percentage': total / self.total_appearances * 100 if self.total_appearances else 0,
          'icon': self._find_icon(reward),
          'color': color
        })
      else:
        details = sorted(reward.get('details', []), key=lambda d: (d.get('appearances', 0), d.get('quantity', 0)), reverse=True)
        for detail in details:
          quantity = detail.get('quantity')
          appearances = detail.get('appearances', 0)
          label = f'{int_to_str(quantity)} {base_label}' if quantity is not None else base_label
          data.append({
            'label': label,
            'percentage': appearances / total * 100 if total else 0,
            'icon': icon,
            'color': color
          })
    return data

  # Icon/emoji helpers
  def _resolve_icon(self, reward) -> str:
    raw_icon = self._find_icon(reward)
    return self._get_custom_emoji(raw_icon)

  def _find_icon(self, reward) -> str:
    reward_type = reward.get('type')
    quality = reward.get('quality')
    matched_choice = next((rc for rc in self.reward_choices if rc.get('name') == reward_type), None)
    if matched_choice is None:
      return ''
    if quality is None:
      return matched_choice.get('icon', '')
    try:
      quality_group = next((c for c in matched_choice.get('choices', []) if c.get('name') == 'Quality'), None)
      if quality_group is None:
        return ''
      return next((c.get('icon', '') for c in quality_group.get('choices', []) if c.get('name') == quality), '')
    except Exception:
      return ''
    
  def _get_custom_emoji(self, icon: str):
    if not icon or 'customIcon' not in icon:
      return icon or ''
    try:
      icon_name = icon.split(':')[1]
      return discord.utils.get(self.emojis, name=icon_name) or ''
    except Exception:
      return ''
    
  def _get_emoji_color(self, icon) -> str:
    default = chart_color.get('default')
    if isinstance(icon, discord.Emoji):
      return default
    if not isinstance(icon, str) or not icon:
      return default
    icon_lower = icon.lower()
    if 'customicon' in icon_lower:
      icon_name = icon.split(':')[1] if ':' in icon else ''
      color_entry = chart_color.get(icon_name)
      if isinstance(color_entry, dict):
        slug = self.session.state.level.get('name_slug', '').lower()
        matched = next((k for k in color_entry if k != 'default' and k in slug), None)
        return color_entry.get(matched, color_entry.get('default', default))
      if isinstance(color_entry, str):
        return color_entry
      return default
    for key, value in chart_color.items():
      if isinstance(value, str) and key != 'default' and key in icon_lower:
        return value
    return default
    
  # Reward helpers
  def _append_with_multiple_reward_types(self, reward: dict, icon: str, chart_entry: dict) -> str:
    reward_type = reward.get('type')
    total = reward.get('total_appearances', 0)
    rate = format_float(chart_entry.get('percentage'), 2)
    lines = [f'\n{icon} {chart_entry.get('label')} : {rate}% ({total}) :\n']
    for detail in reward.get('details', []):
      desc = self.session._translate(detail.get('item')) if detail.get('item') is not None else f'{int_to_str(detail.get('quantity'))} {self.session._translate(reward_type)}'
      detail_rate = format_float(detail.get('appearances', 0) / total * 100, 2)
      lines.append(f'{str_gap}• {desc} : {detail_rate}% ({detail.get('appearances')})\n')
    return ''.join(lines)
  
  def _append_with_single_reward_type(self, reward: dict, icon: str) -> str:
    reward_type = reward.get('type')
    quality = reward.get('quality')
    total = reward.get('total_appearances', 0)
    label = self.session._translate(f'{quality} {reward_type}') if quality else self.session._translate(reward_type)
    has_quantity = False
    lines = []
    details = sorted(reward.get('details', []), key=lambda d: (d.get('appearances', 0), d.get('quantity', 0)), reverse=True)
    has_items = any(d.get('item') is not None for d in details)
    if has_items:
      rate_total = format_float(total / self.total_appearances * 100, 2) if self.total_appearances else 0
      lines.append(f'\n{icon} {label} : {rate_total}% ({total}) :\n')
      for detail in details:
        desc = self.session._translate(detail.get('item'))
        detail_rate = format_float((detail.get('appearances') or 0) / total * 100, 2) if total else 0
        lines.append(f'{str_gap}• {desc} : {detail_rate}% ({detail.get("appearances")})\n')
    else:
      for detail in details:
        quantity = detail.get('quantity')
        if quantity is not None:
          has_quantity = True
          quantity_str = int_to_str(quantity)
        else:
          quantity_str = ''
        rate = format_float((detail.get('appearances') or 0) / total * 100, 2)
        lines.append(f'\n{icon} {quantity_str} {label} : {rate}% ({detail.get('appearances')})\n')
      if has_quantity:
        lines.append(self._energy_stats(reward, icon))
    return ''.join(lines)
  
  # Energy stats
  def _energy_stats(self, reward, icon) -> str:
    details = reward.get('details', [])
    total_rewards = sum((d.get('quantity') or 0) * (d.get('appearances') or 0) for d in details)
    average_reward = total_rewards / self.total_appearances
    displayed_avg = format_float(average_reward, 3) if average_reward < 1000 else floor(average_reward)
    reward_type = reward.get('type')
    lines = [f'\n### {self.session.return_msg.get('average')} ###\n']
    lines.append(f'{icon} {displayed_avg} {self.session._translate(reward_type)} {self.session.return_msg.get('per fight')}\n')
    energy_sources = [{'attr': 'standard_energy_cost', 'name': 'solo energy'}, {'attr': 'coop_energy_cost', 'name': 'coop energy'}]
    for source in energy_sources:
      cost = self.session.state.level.get(source.get('attr'))
      if cost is None:
        continue
      try:
        avg_per_energy = average_reward / cost if cost else 0
        displayed = format_float(avg_per_energy, 3) if average_reward < 1000 else floor(avg_per_energy)
        energy = self.session.return_msg.get(source.get('name'))
        energy_per_fight = self.session.return_msg.get(f'energy{'S' if cost == 1 else 'P'}')
        lines.append(f'{str_gap}• {displayed} {self.session.return_msg.get('per')} {energy} ({cost} {energy_per_fight})\n')
      except Exception:
        continue
    return ''.join(lines)
  
  # Chart
  def _chart(self) -> discord.File:
    width_px = 800
    height_px = 550
    dpi = 100
    data = self._get_chart_data()
    labels = [d['label'] for d in data]
    percentages = [d['percentage'] for d in data]
    colors = [d['color'] for d in data]
    fig, ax = plt.subplots(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
    fig.patch.set_facecolor('#2b2d31')
    ax.set_facecolor('#2b2d31')
    bars = ax.bar(labels, percentages, color=colors, edgecolor='none')
    ax.set_title(self.session.state.level_name, fontsize=16, fontweight=700, color='white', pad=15)
    ax.set_ylabel(self.session.return_msg.get('percentage'), color='white')
    ax.tick_params(colors='white')
    ax.set_ylim(0, max(percentages) * 1.2 if percentages else 100)
    for spine in ax.spines.values():
      spine.set_visible(False)
    ax.yaxis.grid(True, color='#3f4147', linewidth=0.8)
    ax.set_axisbelow(True)
    offset = max(percentages) * 0.02 if percentages else 2
    for bar, pct in zip(bars, percentages):
      ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + offset,
        f'{format_float(pct, 2)}%',
        ha='center', va='bottom', color='white', fontsize=9
      )
    plt.xticks(rotation=20, ha='right', color='white')
    plt.tight_layout(pad=1.2)
    if len(self.rewards) == 1:
      reward = self.rewards[0]
      details = reward.get('details', [])
      total_rewards = sum((d.get('quantity') or 0) * (d.get('appearances') or 0) for d in details)
      average = total_rewards / self.total_appearances if self.total_appearances else 0
      displayed_avg = format_float(average, 3) if average < 1000 else floor(average)
      ax.text(0.85, 0.80, f'{self.session.return_msg.get('avg')}\n{displayed_avg}',
        transform=ax.transAxes,
        ha='center',
        va='center',
        color='white',
        fontsize=12,
        bbox=dict(
          boxstyle='round,pad=0.4',
          facecolor='#2b2d31',
          edgecolor='#3f4147'
        )
      )
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return discord.File(buf, filename='rewards_chart.png')