import zipfile, io

with open('C:/Users/chito/AppData/Local/Temp/wa_plugin_v2.zip', 'rb') as f:
    z = zipfile.ZipFile(io.BytesIO(f.read()))
    for name in z.namelist():
        code = z.read(name).decode('utf-8')
        has_h1 = 'preg_match_all' in code and 'h2' in code
        has_og = 'Fallback: primera imagen' in code
        print(f'{name}')
        print(f'  H1 dedup: {has_h1}')
        print(f'  OG fallback: {has_og}')
