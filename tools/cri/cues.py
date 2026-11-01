"""列出 ACB 的音效: python -I cues.py <utf.py 所在目錄> <file.acb>"""
import sys
sys.path.insert(0, sys.argv[1])
from utf import header, sub
b = open(sys.argv[2], 'rb').read(); h = header(b)
names = sub(b, h, 'CueNameTable'); cues = sub(b, h, 'CueTable'); waves = sub(b, h, 'WaveformTable')
print('Name', h.get('Name'), '| cues', len(cues), '| waveforms', len(waves), '| memory AWB bytes', (h.get('AwbFile') or (0, 0))[1],
      '| stream AWB', bool(h.get('StreamAwbHash') and h['StreamAwbHash'][1]))
print('EncodeTypes', sorted(set(w.get('EncodeType') for w in waves)))
for n in sorted(names, key=lambda n: cues[n['CueIndex']]['CueId']):
    c = cues[n['CueIndex']]; print(c['CueId'], n['CueName'], c.get('Length'))
