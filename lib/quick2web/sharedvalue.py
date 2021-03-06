import json

from quick2web.webserver import WebSocketHandler

class SharedValue(WebSocketHandler):

  def __init__(self, value=None, on_change=None, on_open=None, on_close=None):
    self.value = value
    self.connections = set()
    self.open_handlers = list()
    self.close_handlers = list()
    self.change_handlers = list()

    if on_change:
      self.change_handlers.append(on_change)
    if on_open:
      self.open_handlers.append(on_open)
    if on_close:
      self.close_handlers.append(on_close)

  def on_open(self, connection):
    connection.send(json.dumps(self.value))
    self.connections.add(connection)
    self._fire(self.open_handlers, dict(connection=connection))

  def on_close(self, connection):
    self.connections.remove(connection)
    self._fire(self.close_handlers, dict(connection=connection))

  def on_message(self, connection, message):
    self.value = json.loads(message)
    self._fire(self.change_handlers, dict(value=self.value, connection=connection))
    encoded = json.dumps(self.value)
    for other_connection in self.connections:
      other_connection.send(encoded)

  def _fire(self, handlers, args):
    for handler in handlers:
      handler(**args)

