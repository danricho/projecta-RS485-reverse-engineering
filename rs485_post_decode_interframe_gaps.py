import re
import datetime
from rs485_tooling import *

INPUT_LOG_FILE = f"rs485-20250518T082319-live-packets-1-hex-0.05.log"
OUTPUT_LOG_FILE = INPUT_LOG_FILE.replace("live", "post").replace("-1-hex-", "-2-decode-hex-")
OUTPUT_DECODED_CSV = INPUT_LOG_FILE.replace("live", "post").replace("-1-hex-", "-3-decoded-").replace(".log", ".csv")

def log_packet(packet_data, data, timestamp, f):
    if not packet_data:
        return
    if len(packet_data) > 8:
      f.write(f"{timestamp} | {len(packet_data)} | ")
      f.write(f"{' '.join(f'{b:02X}' for b in packet_data)}")
      f.write(f" | {data}\n")
        
    # this is used to find new data
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

    with open(OUTPUT_LOG_FILE, 'w') as f_out:
     with open(OUTPUT_DECODED_CSV, 'w') as f_out_csv:
        
        f_out_csv.write(f"TS (yyyy-mm-dd hh:mm:ss),")
        f_out_csv.write(f"BATT V,")
        f_out_csv.write(f"BATT A,")
        f_out_csv.write(f"BATT SOC,")
        f_out_csv.write(f"OUT V,")
        f_out_csv.write(f"OUT A,")
        f_out_csv.write(f"SOLAR IN V*,")
        f_out_csv.write(f"SOLAR IN A,")
        f_out_csv.write(f"AUX IN V*,")
        f_out_csv.write(f"AUX IN A,")
        f_out_csv.write(f"PMDCS IN V,")
        f_out_csv.write(f"PMDCS OUT V,")
        f_out_csv.write(f"PMDCS A,")
        f_out_csv.write(f"FRESH TANK 1,")
        f_out_csv.write(f"FRESH TANK 2,")
        f_out_csv.write(f"AC CHARGER CURRENT*,")
        f_out_csv.write(f"AC CHARGER ACTIVE*,")

        f_out_csv.write(f"\n")

        rolling_data = {}

        with open(INPUT_LOG_FILE, 'r') as f_in:
            

            for line in f_in:

              match = re.match(r"(2025[0-9]{2}[0-9]{2}T[0-9]{2}[0-9]{2}[0-9]{2}) \| (.*)", line)
              if match:            
                  
                  timestamp = match.group(1)
                  hex_data = match.group(2)
                  packet = bytes.fromhex(hex_data)
                  data = unpack_data(packet)
                  original_rolling_data = rolling_data.copy()
                  rolling_data.update(data)       

                  rolling_data['ac_charger_current_TBC'] = round(-rolling_data.get('PMDCS_current', 0) -rolling_data.get('solar_input_current', 0) +rolling_data.get('battery_current', 0) +rolling_data.get('output_current', 0),2)
                  rolling_data['ac_charger_active_TBC'] = int(rolling_data['ac_charger_current_TBC'] > 15)
                  
                  log_packet(packet, data, timestamp, f_out)                  

                  if original_rolling_data != rolling_data:
                    ts = datetime.datetime.strptime(timestamp, '%Y%m%dT%H%M%S')
                    ts = ts.strftime("%Y-%m-%d %H:%M:%S")
                    f_out_csv.write(f"{ts},")
                    f_out_csv.write(f"{rolling_data.get('battery_voltage','')},")
                    f_out_csv.write(f"{rolling_data.get('battery_current','')},")
                    f_out_csv.write(f"{rolling_data.get('battery_soc','')},")
                    f_out_csv.write(f"{rolling_data.get('output_voltage','')},")
                    f_out_csv.write(f"{rolling_data.get('output_current','')},")
                    f_out_csv.write(f"{rolling_data.get('solar_input_voltage_TBC','')},")
                    f_out_csv.write(f"{rolling_data.get('solar_input_current','')},")
                    f_out_csv.write(f"{rolling_data.get('aux_input_voltage_TBC','')},")
                    f_out_csv.write(f"{rolling_data.get('aux_input_current','')},")
                    f_out_csv.write(f"{rolling_data.get('PMDCS_input_voltage','')},")
                    f_out_csv.write(f"{rolling_data.get('PMDCS_output_voltage','')},")
                    f_out_csv.write(f"{rolling_data.get('PMDCS_current','')},")
                    f_out_csv.write(f"{rolling_data.get('fresh_tank_1_pc','')},")
                    f_out_csv.write(f"{rolling_data.get('fresh_tank_2_pc','')},")
                    f_out_csv.write(f"{rolling_data.get('ac_charger_current_TBC','')},")
                    f_out_csv.write(f"{rolling_data.get('ac_charger_active_TBC','')},")
                    f_out_csv.write(f"\n")

if __name__ == "__main__":
    main()
