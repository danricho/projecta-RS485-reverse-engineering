import re
import datetime
from rs485_tooling import *

# Input/output filenames
INPUT_LOG_FILE = "rs485-20250518T082319-live-packets-1-hex-0.05.log"
OUTPUT_LOG_FILE = INPUT_LOG_FILE.replace("live", "post").replace("-1-hex-", "-2-decode-hex-")
OUTPUT_DECODED_CSV = INPUT_LOG_FILE.replace("live", "post").replace("-1-hex-", "-3-decoded-").replace(".log", ".csv")

def log_packet(packet_data, data, timestamp, f):
    """
    Writes packet log to file and optionally prints decoded data.
    """
    if not packet_data:
        return
    if len(packet_data) > 8:
        f.write(f"{timestamp} | {len(packet_data)} | {' '.join(f'{b:02X}' for b in packet_data)} | {data}\n")

    # Debug block for locating specific values in packet (disabled by default)
    if False:
        target = 29.88
        tolerance = 0.0
        matches = search_for_value(packet_data, target, tolerance)
        if matches:
            print(f'\n{timestamp[-4:-2]}:{timestamp[-2:]} | {len(packet_data)}')
            print(f"RESULT - {target} +/- {tolerance}")
            for offset, val, method in matches:
                print(f"  Offset {offset:03d}: {val:.5f} ({method})")
            print(f"  DATA: {unpack_data(packet_data)}")
    else:
        if len(packet_data) > 8:
            print(f'{timestamp} | {len(packet_data)}')
            if unpack_data(packet_data) != {}:
                print(unpack_data(packet_data))

def main():
    with open(OUTPUT_LOG_FILE, 'w') as f_out, open(OUTPUT_DECODED_CSV, 'w') as f_out_csv:
        # Write CSV header
        f_out_csv.write("TS (yyyy-mm-dd hh:mm:ss),BATT V,BATT A,BATT SOC,OUT V,OUT A,SOLAR IN V*,SOLAR IN A,AUX IN V*,AUX IN A,PMDCS IN V,PMDCS OUT V,PMDCS A,FRESH TANK 1,FRESH TANK 2,AC CHARGER CURRENT*,AC CHARGER ACTIVE*,\n")

        rolling_data = {}

        with open(INPUT_LOG_FILE, 'r') as f_in:
            for line in f_in:
                match = re.match(r"(2025[0-9]{2}[0-9]{2}T[0-9]{2}[0-9]{2}[0-9]{2}) \| (.*)", line)
                if match:
                    timestamp = match.group(1)
                    hex_data = match.group(2)
                    packet = bytes.fromhex(hex_data)
                    data = unpack_data(packet)

                    # Create copy of current data for change detection
                    original_rolling_data = rolling_data.copy()

                    # Update rolling data with latest packet
                    rolling_data.update(data)

                    # Derived field: estimate of AC charger current and activity
                    rolling_data['ac_charger_current_TBC'] = round(
                        -rolling_data.get('PMDCS_current', 0)
                        -rolling_data.get('solar_input_current', 0)
                        +rolling_data.get('battery_current', 0)
                        +rolling_data.get('output_current', 0), 2
                    )
                    rolling_data['ac_charger_active_TBC'] = int(rolling_data['ac_charger_current_TBC'] > 15)

                    # Log raw data
                    log_packet(packet, data, timestamp, f_out)

                    # Only write CSV row if data changed
                    if original_rolling_data != rolling_data:
                        ts = datetime.datetime.strptime(timestamp, '%Y%m%dT%H%M%S').strftime("%Y-%m-%d %H:%M:%S")
                        f_out_csv.write(f"{ts}," + ','.join(str(rolling_data.get(k, '')) for k in [
                            'battery_voltage', 'battery_current', 'battery_soc',
                            'output_voltage', 'output_current',
                            'solar_input_voltage_TBC', 'solar_input_current',
                            'aux_input_voltage_TBC', 'aux_input_current',
                            'PMDCS_input_voltage', 'PMDCS_output_voltage', 'PMDCS_current',
                            'fresh_tank_1_pc', 'fresh_tank_2_pc',
                            'ac_charger_current_TBC', 'ac_charger_active_TBC'
                        ]) + '\n')

if __name__ == "__main__":
    main()
