import discord
from utils.message import Message

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
	for iter in range(0, how_many):
		stars += ':star:'
	return stars

def rank_text(number):
	if number == 1:
		return 'er'
	else:
		return 'ème'
	
def pluriel(list):
	if len(list) > 1:
		return 's'
	return ''

def nick(message):
	nickname = message.user.nick
	if nickname is None:
		nickname = message.user.global_name
	return nickname


def check_message_length(description):
	footer_txt = Message.message('footer')['ok']
	if len(description) + len(footer_txt) > 4096:
		return False
	else:
		return True