import spi, pickle, json
import RPi.GPIO as GPIO
from quick2web import WebServer, SharedValue

def main():
  # Specify GPIO mode
  GPIO.setmode(GPIO.BOARD)
  
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
  # Set GPIOs to 10 to address separate LED graph
  GPIO.output(11, 1)
  GPIO.output(12, 0)
  print "Volume value: ", value
  print spi.transfer(get_led_level(int(value)))
  # Set GPIO to 00 to select DAC
  GPIO.output(11, 0)
  GPIO.output(12, 0)
  print spi.transfer(get_dac_level(0,int(value)))

def volume_open(connection):
  # Open and configure SPI interface
  status = spi.openSPI(speed=1000000, mode=0)
  print "Volume SPI configuration: ",status
  GPIO.setup(11, GPIO.OUT)
  GPIO.setup(12, GPIO.OUT)
  print 'GPIOs initialized'


###    TONE FUNCTIONS    ###
def tone_updated(value, connection):
  # Set GPIOs to 01 to address separate LED graph
  GPIO.output(11, 0)
  GPIO.output(12, 1)
  print "Tone value: ", value
  print spi.transfer(get_led_level(int(value)))
  # Set GPIO to 00 to select DAC
  GPIO.output(11, 0)
  GPIO.output(12, 0)
  print spi.transfer(get_dac_level(1,int(value)))
  print spi.transfer(get_dac_level(2,int(value)))
  
def tone_open(connection):
  # Open and configure SPI interface
  status = spi.openSPI(speed=1000000, mode=0)
  print "Tone SPI configuration: ",status
  GPIO.setup(11, GPIO.OUT)
  GPIO.setup(12, GPIO.OUT)
  print 'GPIOs initialized'


###    SUSTAIN FUNCTIONS   ###
def sustain_updated(value, connection):
  # Set GPIOs to 11 to address separate LED graph
  GPIO.output(11, 1)
  GPIO.output(12, 1)
  print "Sustain value: ", value
  print spi.transfer(get_led_level(int(value)))
  # Set GPIO to 00 to select DAC
  GPIO.output(11, 0)
  GPIO.output(12, 0)
  print spi.transfer(get_dac_level(3,int(value)))
  
def sustain_open(connection):
  # Open and configure SPI interface
  status = spi.openSPI(speed=1000000, mode=0)
  print "Sustain SPI configuration: ",status
  GPIO.setup(11, GPIO.OUT)
  GPIO.setup(12, GPIO.OUT)
  print 'GPIOs initialized'


###    CLOSE SPI    ###
def spi_close(connection):
  print "Closing SPI..."
  spi.closeSPI()
  print "Cleaning GPIO..."
  GPIO.cleanup()

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

def get_led_level(value):
  led_division = 6
  exponent = value/led_division
  word = '{0:016b}'.format((2 ** exponent)-1)
  # Split into two 8bit words for transmission    
  word1 = word[0:-8]
  word2 = word[8:]
  # Return tuple in the format ((1st 8 bits, 2nd 8 bits))
  return((int(word1,2),int(word2,2)))

def get_dac_level(dac, value):
  value = value * 655
  binary_val = '{0:016b}'.format(value)
  binary_val1 = binary_val[0:-8]
  binary_val2 = binary_val[8:]
  # Return tuple in the format ((1st 8 bits, 2nd 8 bits))
  return((dac,int(binary_val1,2),int(binary_val2,2)))

if __name__ == '__main__':
  main()
