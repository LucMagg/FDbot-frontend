from dataclasses import dataclass
import discord


@dataclass(slots=True)
class DhjkState():
  rand: int = None
  file: discord.File = None