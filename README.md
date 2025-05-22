# projecta-RS485-reverse-engineering

Reverse engineering the serial protocol used on the RS485 bus of the Projecta PM310-BT4J 12V Power Management System.

## Bluetooth (BLE)

I initially spent a lot of time capturing BLE packets on an Android device running the "IntelliJay PM210&310" app. Decoding this data was semi-successful although it appeared that the data structure changed between connections, and I didn't manage to discover the connection handshakes.

I also tried to decompile the app, however it's data unpacking is done in a flutter/dart VM which I wasn't able to readily decrypt (or make sense of).

## RS-485 Bus

The system uses an RS-485 serial bus to allow communication between the LCD/BT device (PMD-BT4J Monitor) and the main management unit (PM335J-2 Transformer Unit). Tapping into this data is far less complicated as it isn't as complex in its packet structure and isn't protected by Bluetooth pairing handshakes.

In order to extract the data, initially a cheap [RS-485 USB dongle](https://vi.aliexpress.com/item/1005006861954310.html) (based on CH343G chip) was used. An interconnect point (can be found in the system's [PDF manual](https://www.projecta.com.au/ts1721611140/attachments/ProductAttachmentGroup/1/PM310-BT4J%20Instruction%20Manual-IS583%2011-23_Screen.pdf)) was found (between cables PMLCD7Y and PMLCDC) and a matching set of male and female waterproof 4 pin JST [connectors with pigtails](https://vi.aliexpress.com/item/1005004426436379.html) (04T-JWPF-VSLE-S / 04R-JWPF-VSLE-S).

```
                          ┌┐┌┐                       ┌┐┌┐                         
                      RED ││││ WHITE           WHITE ││││ RED                     
            +12V ◄────────┤││├───────────────────────┤││├────────► +12V           
                          ││││                       ││││                         
                   YELLOW ││││ BLUE             BLUE ││││ YELLOW                  
         TO    B ◄────────┤│││──────────────┐┌───────┤││├────────► B    TO        
TRANSFORMER               ││││              ││       ││││               LCD/BT    
       UNIT         WHITE ││││ BLACK        ││ BLACK ││││ WHITE         DEVICE    
 (PM335J-2)    A ◄────────┤│││──────────┐┌──┼┼───────┤││├────────► A    (PMD-BT4J)
                          ││││          ││  ││       ││││                         
                    BLACK ││││ RED      ││  ││   RED ││││ BLACK                   
             GND ◄────────┤│││──────┐┌──┼┼──┼┼───────┤││├────────► GND            
                          ││││      ││  ││  ││       ││││                         
                          └┘└┘      ││  ││  ││       └┘└┘                         
                                    ││  ││  ││                                    
                                 ┌──┴┴──┴┴──┴┴──┐                                 
                                 │ GND  A+  B-  │                                 
                                 └──────────────┘                                 
                                      RS-485                                      
                                    USB DONGLE                                    
```

## Scripts to Discover and Unpack the Data

To set up Python:
```sh
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

To run a script use the `venv/bin/python xxx.py` command.

Both of the below scripts depent on [rs485_tooling.py](rs485_tooling.py) which provides the functions:
  - `search_for_value()`: searches a packet for a known value
  - `unpack_data()`: unpacks data from a packet according to previously discovered packet offsets

### [rs485_live_logger_interframe_gaps.py](rs485_live_logger_interframe_gaps.py)

This script connects to the serial bus and:

- Buffers data until a break of at least 50ms occurs (interframe gap).
- Dumps the current time and the Buffer Hex to a line in a log file.
- Displays any known data in the frames as they occur which is helpful to validate a new unpacking location against the LCD display.

### [rs485_post_decode_interframe_gaps.py](rs485_post_decode_interframe_gaps.py)

This script processes a packet log (from [rs485_live_decode_interframe_gaps.py](rs485_live_decode_interframe_gaps.py)) and:

- creates an updated packet log with known data unpacked and added
- creates a csv of known, unpacked data over time
- allows desktop testing of potential new data (using the search for known value function)

## Next Steps

Eventually, the plan is to convert the Python script used to unpack the data on the bus into CircuitPython compatible code that can run on an ESP-32 based [Seeed Studio XIAO](https://vi.aliexpress.com/item/1005006987272421.html) and interface is using a [Seeed Studio RS-485 Breakout Board for XIAO](https://vi.aliexpress.com/item/1005008158515139.html). This RS-485 board should power the ESP32 and then, when WiFi is connected, the microcontroller will read and unpack the data then push it over WiFi for use.


