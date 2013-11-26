import math, spi, pickle, json, rotary_encoder
import RPi.GPIO as GPIO
from quick2web import WebServer, SharedValue

SPI_SEL1_PIN = 13
SPI_SEL2_PIN = 15
SPI_SEL3_PIN = 8
VOL_ENC_A = 12
VOL_ENC_B = 16
TON_ENC_A = 18
TON_ENC_B = 22
SUS_ENC_A = 7
SUS_ENC_B = 11

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
  print "SPI configuration: ",status
  GPIO.setup(SPI_SEL1_PIN, GPIO.OUT)
  GPIO.setup(SPI_SEL2_PIN, GPIO.OUT)
  GPIO.setup(SPI_SEL3_PIN, GPIO.OUT)
  print 'GPIOs initialized'

###     VOLUME FUNCTIONS    ###
def volume_updated(value, connection):
  print "Volume value: ", value
  print "LED Level: ", spi.transfer(get_led_level(0,1,1,int(value)))
  print "Pot Level: ", spi.transfer(get_pot_level(0,1,0,int(value)))

def volume_open(connection):
  airset_open(connection)
  encoder = rotary_encoder.RotaryEncoder(VOL_ENC_A, VOL_ENC_B)
  GPIO.add_event_detect(VOL_ENC_A, GPIO.BOTH, callback=lambda x: enc_update(volume,encoder,connection))
  GPIO.add_event_detect(VOL_ENC_B, GPIO.BOTH, callback=lambda x: enc_update(volume,encoder,connection))
  # Send initial values
  volume_updated(volume.value, connection)


###    TONE FUNCTIONS    ###
def tone_updated(value, connection):
  print "Tone value: ", value
  print "LED Level: ", spi.transfer(get_led_level(0,0,1,int(value)))
  print "Pot Level: ", spi.transfer(get_pot_level(1,0,0,int(value)))
  
def tone_open(connection):
  airset_open(connection)
  encoder = rotary_encoder.RotaryEncoder(TON_ENC_A, TON_ENC_B)
  GPIO.add_event_detect(TON_ENC_A, GPIO.BOTH, callback=lambda x: enc_update(tone,encoder,connection))
  GPIO.add_event_detect(TON_ENC_B, GPIO.BOTH, callback=lambda x: enc_update(tone,encoder,connection))
  # Send initial values
  tone_updated(tone.value, connection)


###    SUSTAIN FUNCTIONS   ###
def sustain_updated(value, connection):
  print "Sustain value: ", value
  print "LED Level: ", spi.transfer(get_led_level(0,0,0,int(value)))
  print "Pot Level: ", spi.transfer(get_pot_level(1,0,1,int(value)))
  
def sustain_open(connection):
  airset_open(connection)
  encoder = rotary_encoder.RotaryEncoder(SUS_ENC_A, SUS_ENC_B)
  GPIO.add_event_detect(SUS_ENC_A, GPIO.BOTH, callback=lambda x: enc_update(sustain,encoder,connection))
  GPIO.add_event_detect(SUS_ENC_B, GPIO.BOTH, callback=lambda x: enc_update(sustain,encoder,connection))
  # Send initial values
  sustain_updated(sustain.value, connection)


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

def get_led_level(sel3, sel2, sel1, value):
  # Set GPIOs to address separate LED graph
  GPIO.output(SPI_SEL1_PIN, sel1)
  GPIO.output(SPI_SEL2_PIN, sel2)
  GPIO.output(SPI_SEL3_PIN, sel3)
  led_division = 6
  exponent = value/led_division
  word = '{0:016b}'.format((2 ** exponent)-1)
  # Split into two 8bit words for transmission    
  word1 = word[0:-8]
  word2 = word[8:]
  # Return tuple in the format ((1st 8bits, 2nd 8bits))
  return((int(word1,2),int(word2,2)))

def get_pot_level(sel3, sel2, sel1, value):
  # Set GPIOs to address separate digital pots
  GPIO.output(SPI_SEL1_PIN, sel1)
  GPIO.output(SPI_SEL2_PIN, sel2)
  GPIO.output(SPI_SEL3_PIN, sel3)
  value = int(math.ceil(value*2.55))
  # Return tuple in the format ((8bits))
  return((0,value))

if __name__ == '__main__':
  main()
