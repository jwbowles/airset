import spi, pickle, json
from quick2web import WebServer, SharedValue

def main():
  webserver = WebServer(port=8888, debug=True)

  webserver.websocket('/volume-value',
      SharedValue(20, on_change=volume_updated, on_open=volume_open, on_close=spi_close))
  webserver.websocket('/tone-value',
      SharedValue(20, on_change=tone_updated, on_open=tone_open, on_close=spi_close))
  webserver.websocket('/sustain-value',
      SharedValue(20, on_change=sustain_updated, on_open=sustain_open, on_close=spi_close))
  webserver.websocket('/save-preset',
      SharedValue(value=read_preset(), on_change=save_preset))
  webserver.websocket('/get-preset',
      SharedValue(on_change=get_preset))

  webserver.static_files('/', './static')
  print('Listening on %s' % webserver.url)
  webserver.run()

###     VOLUME FUNCTIONS    ###
def volume_updated(value, connection):
  # TODO: Communicate with LED bar graph
  print "Volume value: ", value
  print spi.transfer((0x00, int(value)))

def volume_open(connection):
  # Open and configure SPI interface
  status = spi.openSPI(speed=1000000, mode=0)
  print "Volume SPI configuration: ",status


###    TONE FUNCTIONS    ###
def tone_updated(value, connection):
  print "Tone value: ", value
  print spi.transfer((0x00, int(value)))
  
def tone_open(connection):
  # Open and configure SPI interface
  status = spi.openSPI(speed=1000000, mode=0)
  print "Tone SPI configuration: ",status


###    SUSTAIN FUNCTIONS   ###
def sustain_updated(value, connection):
  print "Sustain value: ", value
  print spi.transfer((0x00, int(value)))
  
def sustain_open(connection):
  # Open and configure SPI interface
  status = spi.openSPI(speed=1000000, mode=0)
  print "Sustain SPI configuration: ",status


###    CLOSE SPI    ###
def spi_close(connection):
  print "Closing SPI..."
  spi.closeSPI()

###    SAVE PRESET   ###
def save_preset(value, connection):
  print "Saving Preset...", value
  f = open('preset.txt', 'w')
  pickle.dump(value, f)
  f.close()

def read_preset():
  try:
    f = open('preset.txt', 'r')
  except IOError:
    print "File Not Found!"
    preset = None
  else:
    preset = pickle.load(f)
    f.close()
  return preset

###    GET PRESET   ###
def get_preset(value, connection):
  print "Preset Set!"
  print value

if __name__ == '__main__':
  main()
