import serial
import time
from rs485_tooling import *

# -------------------- Configuration --------------------
PORT = 'COM6'                # Serial port to connect to
BAUDRATE = 9600              # Baud rate (determined experimentally)
SILENCE_THRESHOLD = 0.05     # Threshold in seconds to detect end of a packet (50ms of silence)
timestamp = time.strftime('%Y%m%dT%H%M%S')  # Generate a timestamp for the log file name
LOG_FILE = f'rs485-{timestamp}-live-packets-1-hex-{SILENCE_THRESHOLD}.log'

def log_packet(packet_data):
    """
    Logs a completed packet to file and optionally unpacks it if it looks like a known format.
    """
    if not packet_data:
        return

    # Timestamp for this packet
    timestamp = time.strftime('%Y%m%dT%H%M%S')

    # Log raw packet data in hex format
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} | {' '.join(f'{b:02X}' for b in packet_data)}\n")

    print(f'Logged packet: {timestamp} | {len(packet_data)}')

    # Optionally decode the packet if it’s large enough to match known formats
    if len(packet_data) > 8:
        print(unpack_data(packet_data))


def main():
    # Open the serial port with a non-blocking timeout
    ser = serial.Serial(PORT, BAUDRATE, timeout=0)
    buffer = bytearray()        # Buffer to accumulate incoming data
    last_data_time = None       # Timestamp of the last received data

    print(f"Listening on {PORT} at {BAUDRATE} baud...")

    try:
        while True:
            data = ser.read(1024)         # Read up to 1024 bytes without blocking
            now = time.monotonic()        # Monotonic clock for reliable timing

            if data:
                buffer.extend(data)       # Add received data to buffer
                last_data_time = now      # Update timestamp of last data received

            elif buffer and last_data_time and (now - last_data_time) >= SILENCE_THRESHOLD:
                # If no new data for longer than the silence threshold → packet is complete
                log_packet(buffer)
                buffer.clear()            # Clear buffer for the next packet
                last_data_time = None     # Reset timer

            time.sleep(0.001)  # Small delay to reduce CPU load

    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
    finally:
        ser.close()  # Ensure the serial port is closed properly


if __name__ == "__main__":
    main()
