import serial
import time
from rs485_tooling import *

# Configuration
PORT = 'COM6'
BAUDRATE = 9600 # experimentally found
SILENCE_THRESHOLD = 0.05  # 50 milliseconds
timestamp = time.strftime('%Y%m%dT%H%M%S')
LOG_FILE = f'rs485-{timestamp}-live-packets-1-hex-{SILENCE_THRESHOLD}.log'

def log_packet(packet_data):
    if not packet_data:
        return
    timestamp = time.strftime('%Y%m%dT%H%M%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} | {' '.join(f'{b:02X}' for b in packet_data)}\n")
    print(f'Logged packet: {timestamp} | {len(packet_data)}')
    if len(packet_data) > 8:
      print(unpack_data(packet_data))

def main():
    ser = serial.Serial(PORT, BAUDRATE, timeout=0)
    buffer = bytearray()
    last_data_time = None

    print(f"Listening on {PORT} at {BAUDRATE} baud...")

    try:
        while True:
            data = ser.read(1024)  # Read up to 1024 bytes, non-blocking
            now = time.monotonic()

            if data:
                buffer.extend(data)
                last_data_time = now
            elif buffer and last_data_time and (now - last_data_time) >= SILENCE_THRESHOLD:
                # No new data for 50ms → consider it end of packet
                log_packet(buffer)                
                buffer.clear()
                last_data_time = None

            time.sleep(0.001)  # Small delay to reduce CPU usage

    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
