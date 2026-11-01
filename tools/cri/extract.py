"""把 ACB(+AWB) 裡每個音效解成 mp3, 並輸出 cues.json。
用法: python -I extract.py <tools/cri 目錄> <file.acb> <file.awb 或 -> <輸出目錄> <hca2wav 路徑> <ffmpeg 路徑>
ADX(第 9 型加密) -> adxdec 解密 -> ffmpeg; HCA -> hca2wav。金鑰預設 maimai DX。"""
import sys, struct, json, os, subprocess
sys.path.insert(0, sys.argv[1])
from utf import header, sub
import adxdec
acb_path, awb_path, out, hca2wav, ffmpeg = sys.argv[2:7]
KEY = '%016X' % adxdec.MAIMAI_DX_KEY
b = open(acb_path, 'rb').read(); h = header(b)
def data(v): return b[v[0]:v[0] + v[1]] if v else b''
names = sub(b, h, 'CueNameTable'); cues = sub(b, h, 'CueTable'); seqs = sub(b, h, 'SequenceTable')
tracks = sub(b, h, 'TrackTable'); tev = sub(b, h, 'TrackEventTable'); synths = sub(b, h, 'SynthTable'); waves = sub(b, h, 'WaveformTable')
def u16s(d): return [struct.unpack_from('>H', d, i)[0] for i in range(0, len(d) - 1, 2)]
def cmds(d):
    p = 0
    while p + 3 <= len(d):
        code, sz = struct.unpack_from('>HB', d, p); yield code, d[p + 3:p + 3 + sz]; p += 3 + sz
def resolve(rt, ri, seen, outl):
    """Cue 參照 -> waveform 索引清單 (1=waveform 2=synth 3=sequence)"""
    if (rt, ri) in seen: return
    seen.add((rt, ri))
    if rt == 1: outl.append(ri)
    elif rt == 2:
        it = data(synths[ri]['ReferenceItems'])
        for i in range(0, len(it) - 3, 4): resolve(*struct.unpack_from('>HH', it, i), seen, outl)
    elif rt == 3:
        for ti in u16s(data(seqs[ri]['TrackIndex'])):
            for code, pl in cmds(data(tev[tracks[ti]['EventIndex']]['Command'])):
                if code in (2000, 2003) and len(pl) >= 4: resolve(*struct.unpack_from('>HH', pl, 0), seen, outl)
def afs2(a):
    if not a or a[:4] != b'AFS2': return {}
    n, align = struct.unpack_from('<IH', a, 8); isz, osz = a[6], a[5]
    ids = [int.from_bytes(a[16 + i * isz:16 + (i + 1) * isz], 'little') for i in range(n)]
    ob = 16 + n * isz; offs = [int.from_bytes(a[ob + i * osz:ob + (i + 1) * osz], 'little') for i in range(n + 1)]
    return {ids[i]: a[(offs[i] + align - 1) // align * align:offs[i + 1]] for i in range(n)}
mem = afs2(data(h.get('AwbFile'))); stream = afs2(open(awb_path, 'rb').read() if awb_path != '-' else b'')
os.makedirs(out + '/audio', exist_ok=True)
def convert(raw, fn):
    tmp = out + '/tmp.wav'
    if raw[:2] == b'\x80\x00':
        open(out + '/tmp.adx', 'wb').write(adxdec.decrypt(raw))
        if subprocess.run([ffmpeg, '-loglevel', 'error', '-y', '-f', 'adx', '-i', out + '/tmp.adx', tmp]).returncode: return False
    else:
        open(out + '/tmp.hca', 'wb').write(raw)
        if subprocess.run([hca2wav, out + '/tmp.hca', tmp, KEY], capture_output=True).returncode: return False
    return subprocess.run([ffmpeg, '-loglevel', 'error', '-y', '-i', tmp, '-c:a', 'libmp3lame', '-b:a', '128k', out + '/audio/' + fn]).returncode == 0
done = {}; items = []
for n in sorted(names, key=lambda n: cues[n['CueIndex']]['CueId']):
    c = cues[n['CueIndex']]; ws = []
    resolve(c['ReferenceType'], c['ReferenceIndex'], set(), ws)
    files = []
    for wi in dict.fromkeys(ws):
        w = waves[wi]
        src, aid = ('s', w['StreamAwbId']) if w.get('Streaming') in (1, 2) and w.get('StreamAwbId') not in (None, 65535) else ('m', w['MemoryAwbId'])
        fn = '%s%03d.mp3' % (src, aid)
        if fn not in done:
            raw = (stream if src == 's' else mem).get(aid)
            done[fn] = bool(raw) and convert(raw, fn)
        if done[fn] and fn not in files: files.append(fn)
    ln = c.get('Length')
    items.append({'id': c['CueId'], 'name': n['CueName'], 'len': None if ln in (None, 0, 0xFFFFFFFF) else ln / 1000, 'files': files})
for f in ('tmp.wav', 'tmp.adx', 'tmp.hca'):
    if os.path.exists(out + '/' + f): os.remove(out + '/' + f)
json.dump({'cues': items}, open(out + '/cues.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('cues', len(items), 'with audio', sum(1 for i in items if i['files']), 'decoded', sum(done.values()), 'failed', [k for k, v in done.items() if not v][:10])
