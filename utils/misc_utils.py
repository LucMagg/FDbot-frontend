import discord
from typing import Union, List


def get_discord_color(color: str):
	"""renvoie la couleur Discord en fonction de color"""
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


def stars(how_many):
	stars = ''
	for i in range(0, how_many):
		stars += ':star:'
	return stars

def rank_text(number):
	match number:
		case 1:
			return 'st'
		case 2:
			return 'nd'
		case 3:
			return 'rd'
	return 'th'

def nick(message: discord.message) -> str:
	nickname = message.user.nick
	if nickname is None:
		nickname = message.user.global_name
	return nickname