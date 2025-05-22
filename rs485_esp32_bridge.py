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

WIFI_SSID = "your-ssid"                 # Replace with your Wi-Fi SSID
WIFI_PASSWORD = "your-password"         # Replace with your Wi-Fi password
HTTP_ENDPOINT = "http://your-server.com/rs485"  # HTTP server endpoint to post data

RECONNECT_DELAY = 30                    # Delay between Wi-Fi reconnect attempts (seconds)
SLEEP_MODE = "deep"                     # Options: "off", "light", "deep" — controls power saving
UART_BAUDRATE = 9600                    # Serial baudrate for RS-485
UART_TIMEOUT = 0.01                     # Non-blocking read timeout for UART
PACKET_GAP = 0.05                       # Time gap (seconds) to mark end of packet
# ===============================

# -------------------------------
# Set up UART for RS-485 communication
# -------------------------------
uart = busio.UART(
    tx=board.TX,                      # Use board-defined TX pin
    rx=board.RX,                      # Use board-defined RX pin
    baudrate=UART_BAUDRATE,
    timeout=UART_TIMEOUT              # Quick timeout to keep loop responsive
)

# -------------------------------
# Function to unpack RS-485 packet data into structured values
# -------------------------------
def unpack_data(packet):
    data = {}

    # PMDCS packet format (44 bytes long)
    if len(packet) == 44:
        data['PMDCS_input_voltage'] = int.from_bytes(packet[16:18], 'big', signed=True) / 100.0
        data['PMDCS_output_voltage'] = int.from_bytes(packet[20:22], 'big', signed=True) / 100.0
        data['PMDCS_current'] = int.from_bytes(packet[22:24], 'big', signed=True) / 100.0

    # 102-byte packet (often with 8-byte prefix, which is trimmed)
    if len(packet) == 102:
        packet = packet[8:]

    # Main telemetry packet (94 bytes)
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

# -------------------------------
# Attempt to connect to Wi-Fi
# -------------------------------
def connect_wifi():
    try:
        wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
        print("Connected to Wi-Fi:", wifi.radio.ipv4_address)
        return True
    except Exception as e:
        print("Wi-Fi connection failed:", e)
        return False

# -------------------------------
# Sleep wrapper depending on mode
# -------------------------------
def sleep_mode(delay):
    print(f"Sleeping for {delay} seconds using mode: {SLEEP_MODE}")
    alarm_time = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + delay)

    if SLEEP_MODE == "light":
        alarm.light_sleep_until_alarms(alarm_time)
    elif SLEEP_MODE == "deep":
        alarm.exit_and_deep_sleep_until_alarms(alarm_time)
    else:
        time.sleep(delay)

# -------------------------------
# Initial Wi-Fi connection
# If it fails, enter sleep cycle
# -------------------------------
if not wifi.radio.connected and not connect_wifi():
    sleep_mode(RECONNECT_DELAY)

# -------------------------------
# Main operation loop
# -------------------------------
if wifi.radio.connected:
    # Set up HTTP client session
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, None)

    buffer = bytearray()               # Holds current incoming packet
    last_rx = time.monotonic()        # Timestamp of last byte received

    while True:
        data = uart.read(1)           # Read one byte at a time
        now = time.monotonic()

        if data:
            buffer += data
            last_rx = now
        elif buffer and (now - last_rx) > PACKET_GAP:
            # A packet has finished (idle > PACKET_GAP)
            print("Packet received:", buffer)

            try:
                unpacked = unpack_data(buffer)

                if unpacked:
                    print("Unpacked data:", unpacked)
                    response = requests.post(HTTP_ENDPOINT, json=unpacked)
                    print("Posted:", response.status_code)
                    response.close()
                else:
                    print("Ignored packet (invalid or unrecognized format).")

            except Exception as e:
                print("Error while processing packet:", e)

            buffer = bytearray()  # Reset for next packet

        # If Wi-Fi drops during operation, sleep and retry
        if not wifi.radio.connected:
            print("Wi-Fi connection lost.")
            sleep_mode(RECONNECT_DELAY)
            connect_wifi()

        time.sleep(0.005)  # Small delay to reduce CPU load

# -------------------------------
# Fallback if no Wi-Fi from start
# -------------------------------
else:
    print("Initial Wi-Fi failed. Entering sleep.")
    sleep_mode(RECONNECT_DELAY)
