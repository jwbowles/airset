import spi, pickle, json, rotary_encoder
import RPi.GPIO as GPIO
from quick2web import WebServer, SharedValue

SPI_SEL1_PIN = 13
SPI_SEL2_PIN = 15
ENC1A_PIN = 12
ENC1B_PIN = 16
ENC2A_PIN = 18
ENC2B_PIN = 22
ENC3A_PIN = 7
ENC3B_PIN = 11

volume = SharedValue(20)
tone = SharedValue(20)
sustain = SharedValue(20)

def main():
  try:
    # Specify GPIO mode
    GPIO.setmode(GPIO.BOARD)
    
    webserver = WebServer(port=8888, debug=True)
    
    volume.change_handlers.append(volume_updated)
    volume.open_handlers.append(volume_open)
    volume.close_handlers.append(airset_close)
    tone.change_handlers.append(tone_updated)
    tone.open_handlers.append(tone_open)
    tone.close_handlers.append(airset_close)
    sustain.change_handlers.append(sustain_updated)
    sustain.open_handlers.append(sustain_open)
    sustain.close_handlers.append(airset_close)

    webserver.websocket('/volume-value',volume)
    webserver.websocket('/tone-value',tone)
    webserver.websocket('/sustain-value',sustain)
    webserver.websocket('/save-preset',
        SharedValue(value=read_preset(), on_change=save_preset))
    webserver.websocket('/get-preset',
        SharedValue(on_change=get_preset))

    webserver.static_files('/', './static')
    print('Listening on %s' % webserver.url)
    webserver.run()
    
  except (KeyboardInterrupt, SystemExit):
    print "Closing SPI..."
    spi.closeSPI()
    print "Cleaning GPIO..."
    GPIO.cleanup()

  

def enc_update(shared_value,encoder,connection):
  delta = encoder.get_cycles() # returns 0,1,or -1
  if delta!=0:
    print "rotate %d" % delta
    if int(shared_value.value) < 1:
      shared_value.value = 1
    elif int(shared_value.value) > 99:
      shared_value.value = 99
    else:
      shared_value.value = int(shared_value.value) + delta
      shared_value._fire(shared_value.change_handlers, dict(value=shared_value.value, connection=connection))
      encoded = json.dumps(shared_value.value)
      for other_connection in shared_value.connections:
        other_connection.send(encoded)
  
def airset_open(connection):
  # Open and configure SPI interface
  status = spi.openSPI(speed=1000000, mode=0)
  print "Volume SPI configuration: ",status
  GPIO.setup(SPI_SEL1_PIN, GPIO.OUT)
  GPIO.setup(SPI_SEL2_PIN, GPIO.OUT)
  print 'GPIOs initialized'

###     VOLUME FUNCTIONS    ###
def volume_updated(value, connection):
  print("Shared Value %d" % int(volume.value))
  # Set GPIOs to 10 to address separate LED graph
  GPIO.output(SPI_SEL1_PIN, 1)
  GPIO.output(SPI_SEL2_PIN, 0)
  print "Volume value: ", value
  print spi.transfer(get_led_level(int(value)))
  # Set GPIO to 00 to select DAC
  GPIO.output(SPI_SEL1_PIN, 0)
  GPIO.output(SPI_SEL2_PIN, 0)
  print spi.transfer(get_dac_level(0,int(value)))

def volume_open(connection):
  airset_open(connection)
  encoder = rotary_encoder.RotaryEncoder(ENC1A_PIN, ENC1B_PIN)
  GPIO.add_event_detect(ENC1A_PIN, GPIO.BOTH, callback=lambda x: enc_update(volume,encoder,connection))
  GPIO.add_event_detect(ENC1B_PIN, GPIO.BOTH, callback=lambda x: enc_update(volume,encoder,connection))


###    TONE FUNCTIONS    ###
def tone_updated(value, connection):
  # Set GPIOs to 01 to address separate LED graph
  GPIO.output(SPI_SEL1_PIN, 0)
  GPIO.output(SPI_SEL2_PIN, 1)
  print "Tone value: ", value
  print spi.transfer(get_led_level(int(value)))
  # Set GPIO to 00 to select DAC
  GPIO.output(SPI_SEL1_PIN, 0)
  GPIO.output(SPI_SEL2_PIN, 0)
  print spi.transfer(get_dac_level(1,int(value)))
  print spi.transfer(get_dac_level(2,int(value)))
  
def tone_open(connection):
  airset_open(connection)
  encoder = rotary_encoder.RotaryEncoder(ENC2A_PIN, ENC2B_PIN)
  GPIO.add_event_detect(ENC2A_PIN, GPIO.BOTH, callback=lambda x: enc_update(tone,encoder,connection))
  GPIO.add_event_detect(ENC2B_PIN, GPIO.BOTH, callback=lambda x: enc_update(tone,encoder,connection))


###    SUSTAIN FUNCTIONS   ###
def sustain_updated(value, connection):
  # Set GPIOs to 11 to address separate LED graph
  GPIO.output(SPI_SEL1_PIN, 1)
  GPIO.output(SPI_SEL2_PIN, 1)
  print "Sustain value: ", value
  print spi.transfer(get_led_level(int(value)))
  # Set GPIO to 00 to select DAC
  GPIO.output(SPI_SEL1_PIN, 0)
  GPIO.output(SPI_SEL2_PIN, 0)
  print spi.transfer(get_dac_level(3,int(value)))
  
def sustain_open(connection):
  airset_open(connection)
  encoder = rotary_encoder.RotaryEncoder(ENC3A_PIN, ENC3B_PIN)
  GPIO.add_event_detect(ENC3A_PIN, GPIO.BOTH, callback=lambda x: enc_update(sustain,encoder,connection))
  GPIO.add_event_detect(ENC3B_PIN, GPIO.BOTH, callback=lambda x: enc_update(sustain,encoder,connection))


###    CLOSE SPI    ###
def airset_close(connection):
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
  # Return tuple in the format ((1st 8bits, 2nd 8bits))
  return((int(word1,2),int(word2,2)))

def get_dac_level(dac, value):
  value = value * 655
  binary_val = '{0:016b}'.format(value)
  binary_val1 = binary_val[0:-8]
  binary_val2 = binary_val[8:]
  # Return tuple in the format ((DAC selection 2bits, 1st 8bits, 2nd 8bits))
  return((dac,int(binary_val1,2),int(binary_val2,2)))

if __name__ == '__main__':
  main()
