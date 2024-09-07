class Message:
  def __init__(self, bot):
    self.bot = bot

  def message(self, whichone):
    messages = self.bot.static_data.get_messages()

    for message in messages:
      if message['name'] == whichone:
        return message
      
    return {'title': 'Erreur', 'description': f'Aucun message {whichone} trouvé', 'color': 'red'}