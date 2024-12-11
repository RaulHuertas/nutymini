
print("Starting on NML")

GREEN = (0, 255, 0)
OFF = (0, 0, 0)
BLUE = (0, 0, 255)
ORANGE = (234,133,51)
RED = (255, 0, 0)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (128, 128, 0)



def isItOn(cols, rows, keyIndex):
    import time
    nCol = len(cols)
    nRow = len(rows)
    colPins = [None]*nCol 
    rowPins = [None]*nRow 
    import digitalio
    for i in range(nCol):
        colPin = colPins[i] = digitalio.DigitalInOut(cols[i])
        colPin.direction = digitalio.Direction.OUTPUT
        colPin.value = False
    for i in range(nRow):
        rowPin = rowPins[i] = digitalio.DigitalInOut(rows[i])
        rowPin.direction = digitalio.Direction.INPUT
        rowPin.pull = digitalio.Pull.UP

    colIndex = keyIndex % nCol
    rowIndex = keyIndex // nCol
    #Setup the columns. The one active must be low, the rest high
    for c in range(nCol):
        if c == colIndex:
            colPins[c].value = False
        else:
            colPins[c].value = True
    #Final read of the switch
    import time
    time.sleep(0.01)
    returnVal = rowPins[rowIndex].value

    for i in range(nRow):
        rowPins[i].direction = digitalio.Direction.INPUT
        rowPins[i].deinit()

    for i in range(nCol):
        colPins[i].direction = digitalio.Direction.INPUT
        colPins[i].deinit()

    return not returnVal

bleSelectButton = 23
import board
col_pins = (board.D1,board.D2,board.D3,board.D4, board.D5,board.D6,)
row_pins = (board.NFC1, board.NFC2, board.D7,board.D8,)
bleEnabled = isItOn(col_pins, row_pins, bleSelectButton)
#bleEnabled = True
print("BLE enabled: ",bleEnabled)
del isItOn
del board
del col_pins
del row_pins

def initKB():
    
    import board
    global bleEnabled
    col_pins = (board.D1,board.D2,board.D3,board.D4, board.D5,board.D6,)
    row_pins = (board.NFC1, board.NFC2, board.D7,board.D8,)
    from kmk.scanners import DiodeOrientation

    
    
    from kmk.modules.layers import Layers
    from kmk.scanners.keypad import MatrixScanner
    import pwmio
    from time import monotonic
    from math import modf
    from kmk.keys import ConsumerKey, make_key


    diode_orientation = DiodeOrientation.ROW2COL
    keyboard = None
    if bleEnabled:
        from kmk.kmk_keyboard import KMKKeyboard
        class MyKeyboard(KMKKeyboard):
            def __init__(self, col_pins, row_pins):     
                # create and register the scanner
                self.matrix = MatrixScanner(
                    # required arguments:
                    column_pins=col_pins,
                    row_pins=row_pins,
                    # optional arguments with defaults:
                    columns_to_anodes=diode_orientation,
                    interval=0.020,  # Debounce time in floating point seconds
                    max_events=64
                )               
        keyboard = MyKeyboard(col_pins, row_pins)
    else:
        from kmk.kbusb import KMKKeyboard
        class MyKeyboard(KMKKeyboard):
            def __init__(self, col_pins, row_pins):   
                # create and register the scanner
                self.matrix = MatrixScanner(
                    # required arguments:
                    column_pins=col_pins,
                    row_pins=row_pins,
                    # optional arguments with defaults:
                    columns_to_anodes=diode_orientation,
                    interval=0.020,  # Debounce time in floating point seconds
                    max_events=64
                )               
        keyboard = MyKeyboard(col_pins, row_pins)
    


    keyboard.coord_mapping = [
        0,  1,  2,  3,  4,  5, 
        24, 25, 26, 27, 28, 29,                          
        6,  7,  8,  9, 10, 11,
        30, 31, 32, 33, 34, 35,
        12, 13, 14, 15, 16, 17,
        36, 37, 38, 39, 40, 41,
        18, 19, 20, 21, 22, 23,
        42, 43, 44, 45, 46, 47,
    ]

    split = None
    if bleEnabled:
        from kmk.modules.splitbl import SplitBL, SplitSide, SplitRole
        split = SplitBL(
            split_side=SplitSide.LEFT,
            split_role=SplitRole.Secondary,
            debug_enabled = False 
        )
    else:
        from kmk.modules.splituart import SplitUART, SplitSide
        split = SplitUART(
            split_side=SplitSide.LEFT,
            #split_side=None,
            split_target_left=True,
            data_pin = board.D9,#RX
            data_pin2 = board.D10,#TX
            debug_enabled = False
        )
    



    class RGBLayers(Layers):
        def __init__(self, pin, brightness=0.1):
            global bleEnabled
            Layers.__init__(self)
            self.br =brightness
            if not bleEnabled:
                from neopixel import NeoPixel
                self.rgbStrip =  NeoPixel(pin, 23,brightness=self.br , auto_write=False)      
            self.wpmC = 0
            self.wpmHigh = False
            
            self.startTime = monotonic()
            
            self.ledAnimTime = monotonic()
            from digitalio import DigitalInOut, Direction
            self.redLED = pwmio.PWMOut(board.LED_RED, frequency=5000, duty_cycle=0)
            self.greenLED = pwmio.PWMOut(board.LED_GREEN, frequency=5000, duty_cycle=0)
            self.blueLED = pwmio.PWMOut(board.LED_BLUE, frequency=5000, duty_cycle=0)



            self.currentLayer = 0

            #initialize lights
            self.updateLights(  )
            
            #initialize media
            mediaCodes = (
                (0xE2, ('AUDIO_MUTE', 'MUTE')),
                (0xE9, ('AUDIO_VOL_UP', 'VOLU')),
                (0xEA, ('AUDIO_VOL_DOWN', 'VOLD')),
                (0x6F, ('BRIGHTNESS_UP', 'BRIU')),
                (0x70, ('BRIGHTNESS_DOWN', 'BRID')),
                (0xB5, ('MEDIA_NEXT_TRACK', 'MNXT')),
                (0xB6, ('MEDIA_PREV_TRACK', 'MPRV')),
                (0xB7, ('MEDIA_STOP', 'MSTP')),
                (0xCD, ('MEDIA_PLAY_PAUSE', 'MPLY')),
                #(0xB8, ('MEDIA_EJECT', 'EJCT')),
                (0xB3, ('MEDIA_FAST_FORWARD', 'MFFD')),
                (0xB4, ('MEDIA_REWIND', 'MRWD')),
            )

            for code, names in mediaCodes:
                make_key(names=names, constructor=ConsumerKey, code=code)


        def incrWPM(self, inc=1):
            self.wpmC +=  inc

        def resetWPM(self):
            self.wpmC = 0
            

        def activate_layer(self, keyboard, layer, idx=None):
            super().activate_layer(keyboard, layer, idx)
            self.on_layer_change(layer)

        def deactivate_layer(self, keyboard, layer):
            super().deactivate_layer(keyboard, layer)
            self.on_layer_change(keyboard.active_layers[0])

        def updateLights(self):
            
            nowT = monotonic()
            
            #wpmHigh
            if((nowT-self.startTime)>1):#update wmpHigh
                self.startTime = nowT
                wpmHighTH = 11##threshold for what high wpm is
                if(self.wpmC>wpmHighTH):
                    self.wpmHigh = True
                else:
                    self.wpmHigh = False
                self.resetWPM()

            #######################
            ######LEDS status######
            #######################

            if ((nowT-self.ledAnimTime)<0.100):
                return
            
            #blink pulse             
            pulsePosition = (nowT)/2.0 #blink period
            pulseOn = modf(pulsePosition)[0]>0.9 #off cycle
            pulseHighPosition = (nowT)/0.4 #blink period
            pulseHighOn = modf(pulseHighPosition)[0]>0.5 #off cycle
            
            #####BOARD LEDS
            if not bleEnabled:
                if self.wpmHigh :
                    if pulseHighOn:
                        self.rgbStrip[0] = GREEN
                    else:
                        self.rgbStrip[0] = ORANGE
                else:
                    self.rgbStrip[0] = BLUE

            
            #print(layer)
            dtcyc = 30000
            dtcycOff = 65535
            if self.currentLayer == 0:
                if not bleEnabled:
                    self.rgbStrip[1] = PURPLE
                    self.rgbStrip[2] = OFF
                    self.rgbStrip[3] = OFF
                    self.rgbStrip[4] = OFF
                    self.rgbStrip[5] = OFF
                self.redLED.duty_cycle = dtcyc
                self.greenLED.duty_cycle = dtcycOff
                self.blueLED.duty_cycle = dtcycOff
            elif self.currentLayer == 1:
                if not bleEnabled:
                    self.rgbStrip[1] = PURPLE
                    self.rgbStrip[2] = PURPLE 
                    self.rgbStrip[3] = OFF
                    self.rgbStrip[4] = OFF
                    self.rgbStrip[5] = OFF
                self.redLED.duty_cycle = dtcycOff
                self.greenLED.duty_cycle = dtcyc
                self.blueLED.duty_cycle = dtcycOff
            elif self.currentLayer == 2:
                if not bleEnabled:
                    self.rgbStrip[1] = PURPLE
                    self.rgbStrip[2] = PURPLE
                    self.rgbStrip[3] = PURPLE
                    self.rgbStrip[4] = OFF
                    self.rgbStrip[5] = OFF
                self.redLED.duty_cycle = dtcycOff
                self.greenLED.duty_cycle = dtcycOff
                self.blueLED.duty_cycle = dtcyc
            elif self.currentLayer == 3:
                if not bleEnabled:
                    self.rgbStrip[1] = PURPLE
                    self.rgbStrip[2] = PURPLE
                    self.rgbStrip[3] = PURPLE
                    self.rgbStrip[4] = PURPLE
                    self.rgbStrip[5] = OFF    

                self.redLED.duty_cycle = dtcyc
                self.greenLED.duty_cycle = dtcyc
                self.blueLED.duty_cycle = dtcycOff
            elif self.currentLayer == 4:
                if not bleEnabled:
                    self.rgbStrip[1] = PURPLE
                    self.rgbStrip[2] = PURPLE
                    self.rgbStrip[3] = PURPLE
                    self.rgbStrip[4] = PURPLE
                    self.rgbStrip[5] = PURPLE
                self.redLED.duty_cycle = dtcyc
                self.greenLED.duty_cycle = dtcycOff
                self.blueLED.duty_cycle = dtcyc

            
            if not bleEnabled:
                self.rgbStrip.show()
            self.ledAnimTime = nowT

        def before_matrix_scan(self, sandbox):
            super().before_matrix_scan(sandbox)
            self.updateLights()

        def after_matrix_scan(self, keyboard):
            super().after_matrix_scan(keyboard)
            

        def before_hid_send(self, keyboard):
            super().before_hid_send(keyboard)
            if keyboard.hid_pending:
                self.incrWPM(1)     
        def after_hid_send(self, keyboard):
            super().after_hid_send(keyboard)

        def on_layer_change(self, layer):
            nowT = monotonic()
            self.currentLayer = layer
            self.updateLights()
        

    
    
    rgbLayers = RGBLayers(board.D0, 0.03 )

    if bleEnabled:
        from kmk.modules.mouse_keys import MouseKeys 
        mouseKeys = MouseKeys()
        from kmk.modules.power import Power
        power = Power()
        keyboard.modules = [
            split, 
            mouseKeys,
            rgbLayers, 
            power
        ]
    else:
        from kmk.modules.mouse_keys import MouseKeys         
        from kmk.modules.midi import MidiKeys
        keyboard.modules = [
            split, 
            MouseKeys(),
            rgbLayers, 
            MidiKeys()
        ]

    keyboard.coord_mapping =  [
            0,  1,  2,  3,  4,  5, 
            24, 25, 26, 27, 28, 29,
            6,  7,  8,  9, 10, 11,
            30, 31, 32, 33, 34, 35,
            12, 13, 14, 15, 16, 17,
            36, 37, 38, 39, 40, 41,
            18, 19, 20, 21, 22, 23 ,
            42, 43, 44, 45, 46, 47,
        ]

    
    import gc
    gc.collect()
   
    return keyboard


if __name__ == '__main__':
    print("Starting on NML now")
    kb = initKB()
    kb.debug_enabled = False
    from keyAssignations import assignKeys
    kb.keymap = assignKeys()
    del assignKeys
    if bleEnabled:
        from kmk.hid     import HIDModes
        kb.powersave_enable = True
        kb.go(hid_type=HIDModes.BLE )
    else:
        kb.go( )



