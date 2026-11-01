"""CRI @UTF 表格解析(ACB / ACF 用)。parse_utf(bytes, offset) -> (表名, [row dict])"""
import struct
def _rd(fmt, b, o): return struct.unpack_from('>' + fmt, b, o)[0]
def parse_utf(b, base=0):
    if b[base:base+4] != b'@UTF': raise ValueError('not @UTF at %d' % base)
    t = base + 8
    rows_off = _rd('H', b, t + 2) + t; str_off = _rd('I', b, t + 4) + t; data_off = _rd('I', b, t + 8) + t
    name_off = _rd('I', b, t + 12); ncol = _rd('H', b, t + 16); roww = _rd('H', b, t + 18); nrow = _rd('I', b, t + 20)
    def s(o):
        o += str_off; e = b.index(b'\0', o); return b[o:e].decode('utf-8', 'replace')
    def val(ty, p):
        if ty in (0, 1): return (b[p] if ty == 0 else struct.unpack_from('b', b, p)[0]), p + 1
        if ty in (2, 3): return _rd('H' if ty == 2 else 'h', b, p), p + 2
        if ty in (4, 5): return _rd('I' if ty == 4 else 'i', b, p), p + 4
        if ty in (6, 7): return _rd('Q' if ty == 6 else 'q', b, p), p + 8
        if ty == 8: return _rd('f', b, p), p + 4
        if ty == 0xA: return s(_rd('I', b, p)), p + 4
        if ty == 0xB: return (data_off + _rd('I', b, p), _rd('I', b, p + 4)), p + 8
        raise ValueError('column type %x' % ty)
    cols = []; p = t + 24
    for _ in range(ncol):
        fl = b[p]; nm = s(_rd('I', b, p + 1)); p += 5
        st, ty = fl & 0xF0, fl & 0x0F; const = None
        if st == 0x30: const, p = val(ty, p)
        cols.append((nm, st, ty, const))
    rows = []
    for r in range(nrow):
        q = rows_off + r * roww; row = {}
        for nm, st, ty, const in cols:
            if st == 0x50: row[nm], q = val(ty, q)
            elif st == 0x30: row[nm] = const
            else: row[nm] = None
        rows.append(row)
    return s(name_off), rows
def header(b): return parse_utf(b)[1][0]
def sub(b, h, key):
    v = h.get(key)
    return parse_utf(b, v[0])[1] if v and v[1] else []
