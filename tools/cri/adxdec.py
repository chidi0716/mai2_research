"""CRI ADX 第 9 型加密 -> 一般 ADX(之後可用 ffmpeg -f adx 解碼)。
規則出自 vgmstream (meta/adx.c, util/cri_keys.c, coding/adx_decoder.c)。"""
import struct

MAIMAI_DX_KEY = 0x7F4551499DF55E68   # vgmstream adx_keys.h / hca_keys.h: maimai DX Splash (AC)

def derive_key9(key9, subkey=0):
    if subkey:
        key9 = (key9 * ((subkey << 16) | ((~subkey + 2) & 0xFFFF))) & 0xFFFFFFFFFFFFFFFF
    k = key9 - 1
    return (k >> 27) & 0x7fff, ((k >> 12) & 0x7ffc) | 1, ((k << 1) & 0x7fff) | 1

def decrypt(adx, key9=MAIMAI_DX_KEY, subkey=0):
    d = bytearray(adx)
    if d[0:2] != b'\x80\x00' or d[0x12] != 4 or d[0x13] != 9:
        return bytes(d)                       # 不是第 9 型加密 ADX, 原樣返回
    data = struct.unpack_from('>H', d, 2)[0] + 4
    frame, bits, ch = d[5], d[6], d[7]
    samples = struct.unpack_from('>I', d, 0x0c)[0]
    spf = (frame - 2) * 8 // bits             # 每個音框的取樣數(4 bit = 32)
    frames = ((samples + spf - 1) // spf) * ch
    x, mul, add = derive_key9(key9, subkey)
    for i in range(frames):                   # 多聲道交錯的音框共用同一串金鑰流
        p = data + i * frame
        if p + 2 > len(d): break
        v = struct.unpack_from('>H', d, p)[0]
        if not v & 0x8000:                    # 0x8001 等是結尾標記
            struct.pack_into('>H', d, p, (v ^ x) & 0x1fff)   # 只取低 13 位
        x = (x * mul + add) & 0x7fff
    d[0x13] = 0
    return bytes(d)
