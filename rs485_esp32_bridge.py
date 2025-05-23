# CURRENTLY UNTESTED
# WAITING FOR RS485 MODULE FOR ESP32 XIAO

import time
import board
import busio
import wifi
import socketpool
import adafruit_requests
import alarm

# ===============================
# CONFIGURATION SECTION
# ===============================

# Define two Wi-Fi networks (primary and backup)
WIFI_NETWORKS = [
    ("ssid_primary", "password_primary"),  # Replace with your primary Wi-Fi credentials
    ("ssid_backup", "password_backup")     # Replace with your secondary Wi-Fi credentials
]

HTTP_ENDPOINT = "http://your-server.com/rs485"  # HTTP server URL to POST data to

RECONNECT_DELAY = 30                # Seconds to wait before retrying Wi-Fi connection
SLEEP_MODE = "deep"                 # Sleep mode to use if Wi-Fi is unavailable: "off", "light", or "deep"

UART_BAUDRATE = 9600                # Baudrate for RS-485 communication
UART_TIMEOUT = 0.01                 # Timeout for UART read operations (non-blocking)
PACKET_GAP = 0.05                   # Gap (in seconds) between bytes that indicates end of a packet

# ===============================
# HARDWARE INITIALIZATION
# ===============================

# Set up UART for RS-485 communication using TX/RX pins on the board
uart = busio.UART(
    tx=board.TX,
    rx=board.RX,
    baudrate=UART_BAUDRATE,
    timeout=UART_TIMEOUT
)

# Dictionary to accumulate and maintain the most recent values from all packets
overall_data = {}

# ===============================
# PACKET PARSER FUNCTION
# ===============================

def unpack_data(packet):
    """
    Unpacks known RS-485 data packet formats into a dictionary of sensor values.
    """
    data = {}

    # 44-byte packet: PMDCS (power module) format
    if len(packet) == 44:
        data['PMDCS_input_voltage'] = int.from_bytes(packet[16:18], 'big', signed=True) / 100.0
        data['PMDCS_output_voltage'] = int.from_bytes(packet[20:22], 'big', signed=True) / 100.0
        data['PMDCS_current'] = int.from_bytes(packet[22:24], 'big', signed=True) / 100.0

    # 102-byte packet: Same content as 94 byte packet... has an 8-byte prefix (trimmed to get real 94-byte payload)
    if len(packet) == 102:
        packet = packet[8:]

    # 94-byte packet: main telemetry data format
    if len(packet) == 94:
        data['solar_input_voltage_TBC'] = int.from_bytes(packet[4:6], 'big', signed=True) / 100.0
        data['solar_input_current'] = int.from_bytes(packet[6:8], 'big', signed=True) / 100.0
        data['aux_input_voltage_TBC'] = int.from_bytes(packet[12:14], 'big') / 100.0
        data['aux_input_current'] = int.from_bytes(packet[14:16], 'big') / 100.0
        data['output_voltage'] = int.from_bytes(packet[16:18], 'big', signed=True) / 100.0
        data['output_current'] = int.from_bytes(packet[18:20], 'big', signed=True) / 100.0
        data['battery_voltage'] = int.from_bytes(packet[20:22], 'big', signed=True) / 100.0
        data['battery_current'] = int.from_bytes(packet[22:24], 'big', signed=True) / 100.0
        data['battery_soc'] = int.from_bytes(packet[25:26], 'big')
        data['fresh_tank_1_pc'] = int.from_bytes(packet[41:42], 'big')
        data['fresh_tank_2_pc'] = int.from_bytes(packet[43:44], 'big')

    return data

# ===============================
# WI-FI CONNECTION FUNCTION
# ===============================

def connect_wifi():
    """
    Tries to connect to each configured Wi-Fi network in order.
    Returns True if connected, False otherwise.
    """
    for ssid, password in WIFI_NETWORKS:
        try:
            print(f"Attempting Wi-Fi connection to: {ssid}")
            wifi.radio.connect(ssid, password)
            print("Wi-Fi connected:", wifi.radio.ipv4_address)
            return True
        except Exception as e:
            print(f"Failed to connect to {ssid}: {e}")
    return False

# ===============================
# SLEEP HANDLER FUNCTION
# ===============================

def sleep_mode(delay):
    """
    Sleeps for a given number of seconds using the configured power-saving mode.
    """
    print(f"Sleeping for {delay} seconds using mode: {SLEEP_MODE}")
    alarm_time = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + delay)

    if SLEEP_MODE == "light":
        alarm.light_sleep_until_alarms(alarm_time)
    elif SLEEP_MODE == "deep":
        alarm.exit_and_deep_sleep_until_alarms(alarm_time)
    else:
        time.sleep(delay)

# ===============================
# STARTUP: Attempt Wi-Fi connection or sleep
# ===============================

# If not already connected, try connecting. If failed, go to sleep.
if not wifi.radio.connected and not connect_wifi():
    sleep_mode(RECONNECT_DELAY)

# ===============================
# MAIN LOOP
# ===============================

# Only enter main loop if Wi-Fi is connected
if wifi.radio.connected:
    # Set up HTTP client session using the active Wi-Fi connection
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, None)

    # Buffer to accumulate incoming serial bytes into a packet
    buffer = bytearray()
    last_rx = time.monotonic()  # Time when the last byte was received

    while True:
        data = uart.read(1)  # Read one byte at a time from RS-485
        now = time.monotonic()

        if data:
            # If byte is received, add to buffer and reset the timer
            buffer += data
            last_rx = now

        elif buffer and (now - last_rx) > PACKET_GAP:
            # No data received for >50ms => Packet is complete
            print("Packet received:", buffer)

            try:
                unpacked = unpack_data(buffer)

                if unpacked:
                    # Merge new values into overall_data dictionary
                    overall_data.update(unpacked)
                    print("Unpacked data:", unpacked)

                    # Only POST the data if this is a full 94-byte or 102-byte packet
                    if len(buffer) in (94, 102):
                        print("Sending overall data:", overall_data)
                        response = requests.post(HTTP_ENDPOINT, json=overall_data)
                        print("Server response:", response.status_code)
                        response.close()
                else:
                    print("Unrecognized packet format. Skipped.")
            except Exception as e:
                print("Error while processing packet:", e)

            # Clear buffer for the next packet
            buffer = bytearray()

        # Check Wi-Fi connection health
        if not wifi.radio.connected:
            print("Wi-Fi disconnected. Sleeping before retry...")
            sleep_mode(RECONNECT_DELAY)
            connect_wifi()

        # Small delay to prevent tight loop from hogging the CPU
        time.sleep(0.005)

# If Wi-Fi couldn't be established at startup, go to sleep and retry later
else:
    print("Wi-Fi unavailable at startup. Sleeping...")
    sleep_mode(RECONNECT_DELAY)
