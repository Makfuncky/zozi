import os, struct

rec_bin = r'D:\$Recycle.Bin\S-1-5-21-1339371623-4152739331-235715422-1002'

info_files = sorted([f for f in os.listdir(rec_bin) if f.startswith('$I')])
print(f'Found {len(info_files)} info files')

for f in info_files:
    full = os.path.join(rec_bin, f)
    try:
        with open(full, 'rb') as fh:
            data = fh.read()
        # $I file format:
        # 4 bytes: total size of info file (including header)
        # 4 bytes: unknown (possibly flags)
        # 24 bytes: unknown (possibly deletion time or other metadata)
        # 4 bytes: unknown
        # 48 bytes * 2: original filename in UTF-16LE (max 24 chars wide = 48 chars)
        # Actually the format is:
        # offset 0: 4 bytes = size of file
        # offset 4: 4 bytes = unknown
        # offset 8: 24 bytes = unknown
        # offset 32: 4 bytes = unknown
        # offset 36: filename in UTF-16LE (up to remaining bytes)
        
        # Try to extract the original filename
        if len(data) >= 36:
            try:
                # The filename should be at offset 36
                name_bytes = data[36:]
                try:
                    original_name = name_bytes.decode('utf-16-le').rstrip('\x00')
                except:
                    original_name = name_bytes.decode('utf-8', errors='replace').rstrip('\x00')
                
                file_size = struct.unpack('<I', data[0:4])[0]
                
                print(f'{f} -> size={file_size}, original={original_name}')
            except Exception as e:
                print(f'{f} -> parse error: {e}')
    except Exception as e:
        print(f'{f} -> read error: {e}')
