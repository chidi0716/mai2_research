# tools/cri：CRI ADX2 音效工具

用來研究 maimai DX 的 `.acb` / `.awb`：列出音效、解出每個音效、產生試聽網頁。全部是自己寫的小工具，**不含任何遊戲檔案，也不含 vgmstream 原始碼**。

| 檔案 | 用途 |
|---|---|
| `utf.py` | 解析 CRI `@UTF` 表：`header(b)` 讀 ACB 頂層表、`sub(b, h, 'CueTable')` 讀子表、`parse_utf(b, base)` 通用 |
| `cues.py` | 列出 ACB 名稱、音效數、編碼類型、每個音效的 `CueId / 名稱 / 長度(ms)` |
| `adxdec.py` | 把第 9 型加密的 ADX 解密成一般 ADX（之後交給 ffmpeg） |
| `hca2wav.c` | 用 vgmstream 的 clHCA 把（加密的）HCA 解成 WAV |
| `extract.py` | 解析 Cue → Waveform → AWB，全部轉成 mp3，輸出 `cues.json` |
| `page.py` | 用 `cues.json` 產生單檔試聽頁 `index.html`（搜尋、進度條、Space 暫停、Esc 停止） |

## 準備

- Python 3（只用標準函式庫）、`ffmpeg`、`gcc`
- 編譯 `hca2wav`：先從 vgmstream 下載 `src/coding/libs/` 底下的 `clhca.c`、`clhca.h`、`clhca_data.h`，放在同一個資料夾

```bash
for f in clhca.c clhca.h clhca_data.h; do
  curl -sSfO https://raw.githubusercontent.com/vgmstream/vgmstream/master/src/coding/libs/$f
done
gcc -O2 -o hca2wav hca2wav.c clhca.c -lm
```

## 用法

```bash
# 列出音效 (第一個參數是 utf.py 所在目錄; 用 -I 避免從目前資料夾載入模組)
python3 -I cues.py tools/cri Mai2Cue.acb

# 全部解出: <tools/cri> <acb> <awb 或 -> <輸出目錄> <hca2wav> <ffmpeg>
python3 -I extract.py tools/cri Mai2Cue.acb Mai2Cue.awb out ./hca2wav ffmpeg

# 試聽頁
python3 -I page.py out        # 開 out/index.html
```

輸出：`out/audio/m###.mp3`（memory AWB，內嵌在 ACB 裡）、`out/audio/s###.mp3`（stream AWB，外部 `.awb`），`out/cues.json` 是 `{cues:[{id, name, len, files}]}`。

## 驗證紀錄

| 檔案 | 結果 |
|---|---|
| `Mai2Cue.acb/.awb`（遊戲本體） | 488 個音效，ADX 為主、少數 HCA，全部解出 |
| `murasame.acb/.awb`（MaiL2d 語音包） | 92 個音效，其中 47 個有聲音（其餘序列沒有音軌，是語音包本身沒放），HCA，43 個不重複檔案，含 stream AWB |

## 原理摘要

- 音效解析鏈：`CueTable.ReferenceType` 1 = Waveform、2 = Synth、3 = Sequence。Synth 的 `ReferenceItems` 是 `(type, index)` 兩個 u16 一組；Sequence 的 `TrackIndex` → `TrackTable.EventIndex` → `TrackEventTable.Command`，指令碼 2000 / 2003 的參數是 `(type, index)`。
- `WaveformTable.Streaming` 1 / 2 → 讀外部 `.awb` 的 `StreamAwbId`；0 → 讀 ACB 內 `AwbFile` 的 `MemoryAwbId`。
- AWB 是 AFS2：`0x05` 位移欄寬、`0x06` ID 欄寬、`0x08` 數量、`0x0c` 對齊。
- ADX 第 9 型：金鑰流 `x, mul, add` 由 64-bit 金鑰導出，每個音框前 2 位元組的 scale `^= x` 後**只取低 13 位**（`& 0x1fff`，漏掉會變雜音），`x = x*mul + add (mod 0x8000)`；最後把 `0x13` 改成 0。
- HCA：clHCA `SetKey(key)` 後逐 block 解碼，去掉 `encoderDelay` / `encoderPadding`。
- maimai DX 的金鑰 `7F4551499DF55E68`（vgmstream 公開金鑰清單），ADX 與 HCA 共用。

> 解出來的音效是遊戲素材，只在本機研究，不要上傳公開。
