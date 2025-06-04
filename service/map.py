import discord
import os
import io
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

class MapService: 
  def __init__(self, bot):
    self.bot = bot
    self.logger = bot.logger
    self.tiles_size = 150
    self.map_interval = 50
    self.font_color = (200, 200, 40, 255)
    self.font_outline_color = (0, 0, 0, 255)
    self.maps = None
    self.channels = None
    self.tiles_pic = self.get_pics_from_directory(path='images')
    self.font = self.load_font()
    self.image_dict = None
    self.pic = None
    self.header = None
    self.stages_count = None
    self.map_tiles = None
    self.positions = None
    self.gameplay = None
    self.water_or_lava = None

  @classmethod
  async def create(cls, bot):
    instance = cls(bot)
    instance.maps = await instance.load_maps()
    return instance

  def generate_map(self, map):
    self.logger.log_only('debug', 'generating map')
    self.transform_map(map)
    self.map_to_pic()
    with io.BytesIO() as image_binary:
      self.pic.save(image_binary, 'PNG')
      image_binary.seek(0)
      self.logger.log_only('debug', 'map generated')
      return discord.File(fp=image_binary, filename='map.png')
    
  
  def map_to_pic(self):
    if self.map_tiles is None:
      return None
    
    self.set_image_size()
    self.stages_count = max(len(self.map_tiles), len(self.positions))

    if self.gameplay == 'spire':
      if self.stages_count == 1:
        self.add_single_header()
      else:
        self.add_multiple_headers()
    
    for s in range(self.stages_count):
      self.draw_map(s)

  def draw_map(self, stage):
    map = self.map_tiles[stage]
    if len(self.positions) == 0:
      positions = []
    else:
      positions = self.positions[stage]
      
    for y in range(len(map[0])):
      for x in range(len(map)):
        self.draw_tile(map, positions, y, x, stage)

  def draw_tile(self, map, positions, y, x, stage):
    tile_id = map[x][y]['type']
    if tile_id == 'water' and self.water_or_lava:
      tile_id = self.water_or_lava
    tile = self.tiles_pic[tile_id].copy()
    if tile.size != (self.tiles_size, self.tiles_size):
      tile = tile.resize((self.tiles_size, self.tiles_size))
    if map[x][y]['color'] is not None:
      tile = self.color_tile(tile, map[x][y]['color'])        
    if (x, y) in positions:
      tile = self.add_centered_text_to_pic(pic=tile, text=str(positions.index((x, y)) + 1))
    posx = (x + 1) * self.tiles_size
    posy = (y * self.tiles_size) + (stage * len(self.map_tiles[0][0]) * self.tiles_size) + (stage * self.map_interval)
    self.pic.paste(tile, (posy, posx))


  def set_image_size(self):
    width = ((len(self.map_tiles) * len(self.map_tiles[0][0])) * self.tiles_size) + (len(self.map_tiles) - 1) * self.map_interval
    height = (len(self.map_tiles[0]) + 1) * self.tiles_size
    self.pic = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    self.header = Image.new('RGBA', (width, self.tiles_size), (0, 0, 0, 0))
   
  def add_single_header(self):
    text = f'Stages 1, 2, 3'
    self.header = self.add_centered_text_to_pic(self.header, text)
    self.pic.paste(self.header, (0, 0))

  def add_multiple_headers(self):
    for s in range(self.stages_count):
      text = f'Stage {str(s + 1)}'
      width = len(self.map_tiles[0][0]) * self.tiles_size
      header = Image.new('RGBA', (width, self.tiles_size), (0, 0, 0, 0))
      header = self.add_centered_text_to_pic(header, text)
      self.header.paste(header, ((width + self.map_interval) * s, 0))
    self.pic.paste(self.header, (0, 0))

  def add_centered_text_to_pic(self, pic, text):
    pic_width, pic_height = pic.size
    draw_layer = Image.new('RGBA', pic.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(draw_layer)

    left, top, right, bottom = draw.textbbox((0, 0), text, font=self.font)
    text_width = right - left
    text_height = bottom - top

    position = ((pic_width - text_width) // 2 - left, (pic_height - text_height) // 2 - top)
    for offset_x, offset_y in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
      draw.text((position[0] + offset_x, position[1] + offset_y), text, fill=self.font_outline_color, font=self.font)
    draw.text(position, text, fill=self.font_color, font=self.font)
    return Image.alpha_composite(pic, draw_layer)
  
  def color_tile(self, tile, color):
    r, g, b, a = tile.split()
    match color:
      case 'red':
        r = ImageEnhance.Brightness(r).enhance(1.5)
        g = ImageEnhance.Brightness(g).enhance(0.8)
        b = ImageEnhance.Brightness(b).enhance(0.8)
        tile = Image.merge('RGBA', (r, g, b, a))
      case 'green':
        r = ImageEnhance.Brightness(r).enhance(0.8)
        g = ImageEnhance.Brightness(g).enhance(1.5)
        b = ImageEnhance.Brightness(b).enhance(0.8)
        tile = Image.merge('RGBA', (r, g, b, a))
    return tile
  
  def transform_map(self, map):
    rows = len(map.get('map'))
    cols = len(map.get('map')[0])

    if map.get('start') is None:
      self.positions = []
    else:
      self.positions = [[] for _ in range(len(map.get('start')))]
      directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
      for stage in range(len(map.get('start'))):
        for pos in map.get('start')[stage]:
          y = pos[0]
          x = int(pos[1:])
          self.positions[stage].append((x - 1, ord(y) - ord('A')))

    self.stages_count = 1 if len(self.positions) <= 1 else len(self.positions)
    self.map_tiles = [[[None for _ in range(cols)] for _ in range(rows)] for _ in range(self.stages_count)]

    for stage in range(self.stages_count):
      for y in range(cols):
        for x in range(rows):
          if map.get('map')[x][y] == 'square':
            if len(self.positions) == 0:
              if x < rows / 2:
                self.map_tiles[stage][x][y] = {'color': 'red'}
              else:
                self.map_tiles[stage][x][y] = {'color': 'green'}
            else:
              self.map_tiles[stage][x][y] = {'color': 'red'}
            if (x + y) % 2 == 0:
              self.map_tiles[stage][x][y]['type'] = 'light'
            else:
              self.map_tiles[stage][x][y]['type'] = 'dark'
          else:
            self.map_tiles[stage][x][y] = {'type': map.get('map')[x][y], 'color': None}

      if len(self.positions) > 0:
        for x, y in self.positions[stage]:
          if 0 <= x < rows and 0 <= y < cols:
            self.map_tiles[stage][x][y]['color'] = None
          for dy, dx in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < rows and 0 <= ny < cols:
              self.map_tiles[stage][nx][ny]['color'] = None
    self.gameplay = map.get('gameplay').lower()
    self.water_or_lava = map.get('water_or_lava')


  def get_pics_from_directory(self, path: str):
    self.logger.log_only('debug', f'chargement des images du dossier {path}')
    tile_cache = {}
    if not os.path.exists(path):
      error_msg = f'Le dossier {path} n\'existe pas'
      self.logger.log_only('warning', error_msg)
      raise FileNotFoundError(error_msg)
    for filename in os.listdir(path):
      if filename.lower().endswith('.png'):
        tile_id = os.path.splitext(filename)[0]
        tile_path = os.path.join(path, filename)
        try:
          tile_image = Image.open(tile_path).convert('RGBA')
          tile_cache[tile_id] = tile_image
          self.logger.log_only('debug', f'-- {filename} ok')
        except Exception as e:
          self.logger.log_only('warning', f'Erreur lors du chargement de {filename}: {e}')
    if not tile_cache:
      self.logger.log_only('warning', f'Aucune image PNG n\'a été trouvée dans le dossier {path}')
    else:
      self.logger.log_only('debug', f'{len(tile_cache)} images chargées')
    return tile_cache
  
  def load_font(self):
    try:
      return ImageFont.truetype("Arial.ttf", size=self.tiles_size // 2)
    except IOError:
      try:
        return ImageFont.truetype("DejaVuSans.ttf", size=self.tiles_size // 2)
      except IOError:
        return ImageFont.load_default()
      
  async def load_maps(self):
    maps_data = await self.bot.back_requests.call('getAllMaps', False)    
    return maps_data
  
  async def check_maps_in_repos(self):
    self.channels = await self.bot.back_requests.call('getAllChannels', False)
    self.logger.log_only('debug', f'repo channels: {self.channels}')
    if not self.channels:
      return

    for map in self.maps:
      missing_channels = []
      for channel in self.channels.get(map.get('gameplay').lower()):
        map_already_posted_in_channel = None
        if map.get('pic_repository'):
          map_already_posted_in_channel = next((p for p in map.get('pic_repository') if p.get('channel') == channel), None)
        if map_already_posted_in_channel is None:
          channel_id_int = int(channel)
          channel = self.bot.get_channel(channel_id_int)
          if channel is not None:
            missing_channels.append(channel)
          else:
            self.logger.log_only('warning', f"arg : Channel {channel_id_int} non trouvé")
      self.logger.log_only('debug', f'map: {map.get('name')} / to post in: {missing_channels}')
      if len(missing_channels) > 0:
        await self.generate_and_post_in_repo(map, missing_channels)

  async def generate_and_post_in_repo(self, map, missing_channels):
    for channel in missing_channels:
      try:
        map_pic = self.generate_map(map)
        message = await channel.send(content=f'\n # {map.get('name')} #', file=map_pic)
        if map.get('pic_repository') is None:
          map['pic_repository'] = []
        map.get('pic_repository').append({'channel': channel.id, 'url': message.attachments[0].url})
      except:
        self.logger.log_only('warning', f"arg : Erreur lors de l'envoi au channel {channel.id}")
    await self.bot.back_requests.call('updateMap', False, [map])