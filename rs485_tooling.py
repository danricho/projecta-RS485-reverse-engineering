import struct

def search_for_value(data, target, tolerance):
    
    def is_close(val, target, tol):
      return abs(val - target) <= tol

    matches = []

    for i in range(len(data)):
        
        # --- 1-byte fields ---
        if i <= len(data):
            u8_le = struct.unpack('<b', data[i:i+1])[0]
            u8_be = struct.unpack('>b', data[i:i+1])[0]
            i8_le = struct.unpack('<B', data[i:i+1])[0]
            i8_be = struct.unpack('>B', data[i:i+1])[0]

            for value, desc in [
                (u8_le, "uint8 LE"),
                (u8_be, "uint8 BE"),
                (i8_le, "int8 LE"),
                (i8_be, "int8 BE"),
            ]:

                if is_close(value, target, tolerance):
                    matches.append((i, value, desc))

        # --- 2-byte fields ---
        if i + 2 <= len(data):
            u16_le = int.from_bytes(data[i:i+2], 'little')
            u16_be = int.from_bytes(data[i:i+2], 'big')
            i16_le = int.from_bytes(data[i:i+2], 'little', signed=True)
            i16_be = int.from_bytes(data[i:i+2], 'big', signed=True)

            for value, desc in [
                (u16_le / 1000, "uint16 LE / 1000"),
                (u16_le / 100,  "uint16 LE / 100"),
                (u16_be / 1000, "uint16 BE / 1000"),
                (u16_be / 100,  "uint16 BE / 100"),
                (i16_le / 1000, "int16 LE / 1000"),
                (i16_le / 100,  "int16 LE / 100"),
                (i16_be / 1000, "int16 BE / 1000"),
                (i16_be / 100,  "int16 BE / 100"),
            ]:

                if is_close(value, target, tolerance):
                    matches.append((i, value, desc))

        # --- 4-byte fields ---
        if i + 4 <= len(data):
            try:
                f32_le = struct.unpack('<f', data[i:i+4])[0]
                f32_be = struct.unpack('>f', data[i:i+4])[0]

                if is_close(f32_le, target, tolerance):
                    matches.append((i, f32_le, "float32 LE"))

                if is_close(f32_be, target, tolerance):
                    matches.append((i, f32_be, "float32 BE"))

            except:
                pass

            u32_le = int.from_bytes(data[i:i+4], 'little')
            u32_be = int.from_bytes(data[i:i+4], 'big')
            i32_le = int.from_bytes(data[i:i+4], 'little', signed=True)
            i32_be = int.from_bytes(data[i:i+4], 'big', signed=True)

            for value, desc in [
                (u32_le / 1000, "uint32 LE / 1000"),
                (u32_le / 100,  "uint32 LE / 100"),
                (u32_be / 1000, "uint32 BE / 1000"),
                (u32_be / 100,  "uint32 BE / 100"),
                (i32_le / 1000, "int32 LE / 1000"),
                (i32_le / 100,  "int32 LE / 100"),
                (i32_be / 1000, "int32 BE / 1000"),
                (i32_be / 100,  "int32 BE / 100"),
            ]:
                if is_close(value, target, tolerance):
                    matches.append((i, value, desc))

    return matches

def unpack_data(packet):
    data = {}

    if len(packet) == 44:        
        data['PMDCS_input_voltage'] = int.from_bytes(packet[16:18], 'big', signed=True) / 100.0 
        data['PMDCS_output_voltage'] = int.from_bytes(packet[20:22], 'big', signed=True) / 100.0 
        data['PMDCS_current'] = int.from_bytes(packet[22:24], 'big', signed=True) / 100.0 
        
    if len(packet) == 102: # this appears the same as the 94 with a leading 8 bytes
      packet = packet[8:]
    
    if len(packet) == 94:      
        data['solar_input_current'] = int.from_bytes(packet[6:8], 'big', signed=True) / 100.0     
        data['solar_input_voltage_TBC'] = int.from_bytes(packet[4:6], 'big', signed=True) / 100.0 
        data['aux_input_voltage_TBC'] = int.from_bytes(packet[12:14], 'big', signed=False) / 100.0     
        data['aux_input_current'] = int.from_bytes(packet[14:16], 'big', signed=False) / 100.0 
        data['output_voltage'] = int.from_bytes(packet[16:18], 'big', signed=True) / 100.0 
        data['output_current'] = int.from_bytes(packet[18:20], 'big', signed=True) / 100.0 
        data['battery_voltage'] = int.from_bytes(packet[20:22], 'big', signed=True) / 100.0 
        data['battery_current'] = int.from_bytes(packet[22:24], 'big', signed=True) / 100.0 
        data['battery_soc'] = int.from_bytes(packet[25:26], 'big', signed=False)
        data['fresh_tank_1_pc'] = int.from_bytes(packet[41:42], 'big', signed=False)
        data['fresh_tank_2_pc'] = int.from_bytes(packet[43:44], 'big', signed=False)
        
        # time to go (can be derived by battery current and capacity)
        # state of the output controls (Overall Power, Night Mode, Hot Water System, Water Pump)

    return data
