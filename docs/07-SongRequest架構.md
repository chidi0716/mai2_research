# 07 SongRequest（點歌台 mod）架構

原始碼：<https://github.com/chidi0716/maimai-song-request->（fork 自 ZCM-X 原作，MIT）。以下以 v1.1.11 為準。

## 功能

遊戲執行時在電腦上開一個網頁（`http://127.0.0.1:8790/`）：搜歌、點難度，遊戲就跳到那首歌的難度選擇畫面。另有正在遊玩面板、遠端分享（給不同網路的人點歌）。不改任何遊戲檔案。

## 接入點

| 位置 | 方式 | 用途 |
|---|---|---|
| `MusicSelectProcess.OnStart` / `OnRelease` | Harmony Postfix | 記住 / 釋放選曲畫面物件 |
| `_subSequenceArray`、`_currentPlayerSubSequence`、`_beforePlayerSubSequence` | `AccessTools.FieldRefAccess` | 讀子畫面狀態 |
| `SyncNext(SubSequence)` | `AccessTools.MethodDelegate` | 用遊戲自己的方式切到難度畫面 |
| `DataManager`、選曲列表 | 直接讀 + 反射 | 曲庫 |
| `AssetManager` | 直接呼叫 | 封面 |
| `GamePlayManager` 等 | 直接讀 | 正在遊玩的分數、Combo、判定 |
| `OnUpdate` | 每幀 | 處理網頁排進來的工作 |

## 執行緒模型

```
HttpListener 執行緒 ──(排隊)──▶ 主執行緒 OnUpdate ──▶ 遊戲物件 / Unity
        ▲                                  │
        └──── 背景執行緒寫回網頁 ◀───────────┘
```

- 網頁執行緒**只排隊**（`MainThread.Run(work, timeout, fallback)`），主執行緒每幀最多處理 4 件。
- 回寫網頁、SSE 推送用**專用背景執行緒**（不用 ThreadPool，因為 HttpListener 收連線也靠 ThreadPool，被卡住會整個收不到新請求）。每個 SSE 連線一條寫入執行緒，寫入 10 秒逾時就斷。
- 就緒門控：`DataManager.IsLoaded()` 之前什麼都不做。

## 點歌流程（主執行緒）

1. 確認在選曲畫面、目前子畫面是選曲列表或難度畫面、沒有玩家被鎖輸入（切換動畫中最多等 3 秒）。連點只執行最後一首。
2. 在 `CombineMusicDataList` 各分類找曲目（跳過空格、「隨機」格；DX ID 找不到就試 `id % 10000`，再找不到用曲名）；跳過對戰 / 挑戰 / 段位 / 聯機等特殊分類。
3. 已在難度畫面時先 `SyncNext(Music)` 退回。
4. 設 `CurrentCategorySelect` / `CurrentMusicSelect` / `ScoreType` → `ChangeBGM()` → `CalcMonitorDifficulty(true)` → 設 `CurrentDifficulty` / `DifficultySelectIndex`（遊戲判定玩不了就往下退一檔）。
5. 照遊戲「確認選曲」流程收起卡片、鎖輸入 1.2 秒，下一幀 `SyncNext(Difficulty 或 UtageDifficulty)`。

## 曲庫

- 來源：選曲列表 + `DataManager` 內部表等多路讀取，取條目最多的（避開被其他 mod 過濾的 `GetMusics()`）。
- 每首歌的 JSON 拆成「靜態（名稱、等級、定數、別名）」與「動態（DX/STD、可玩與否）」片段快取。
- 變化偵測：在選曲畫面只數各分類條目數；不在選曲畫面每 60 秒才整表重掃。
- 別名庫 `aliases.txt`（MuNET 別名資料），可放在 `Mods\SongRequestMod\` 覆蓋內嵌版本。

## 網頁與 API

`page.html` 內嵌在 DLL（磁碟上有同名檔案時優先）。主要 API：

| 方法 | 路徑 | 用途 |
|---|---|---|
| GET | `/api/songs` | 曲庫 JSON（含 `const` 定數、`maxConst`） |
| POST | `/api/play` | 表單 `id`、`diff`、`type=dx\|std` |
| POST | `/api/random` | 隨機點歌 |
| GET | `/api/status` | 版本、曲目數、`rev`、`jacketGen`、狀態 |
| GET | `/api/npstream` | SSE：正在遊玩即時推送 |
| GET | `/jacket?id=&s=1` | 封面 PNG（主執行緒依時間預算編碼） |
| GET | `/api/perf` | 各段耗時（排查卡頓） |
| GET | `/api/selfcheck` | 自我診斷 |

## 遠端分享

開分享時三條線路同時啟動，成功的都列在面板上：

| 線路 | 原理 |
|---|---|
| Cloudflare 通道 | 啟動 `cloudflared tunnel --url http://127.0.0.1:8790`，取得 `https://*.trycloudflare.com` |
| IPv6 直連 | 本機有公網 IPv6 時在 `[::]:8790` 接連線 |
| IPv4 直連 | TCP STUN 查公網 IP:埠、保活維持 NAT 映射、兩台 STUN 比對排除對稱型 NAT、UPnP 自動通訊埠轉發 |

- 直連線路是 TCP 轉發器：改寫 Host、加 `X-SongRequest-Remote` 標記後轉給 HttpListener；同時連線數上限、10 秒沒送完請求頭就斷。
- 每次開分享產生隨機金鑰，遠端請求必須帶 `?k=`（之後存 cookie）；遠端不能用診斷與分享開關。

## 原始碼結構

| 檔案 | 負責 |
|---|---|
| `Mod.cs` | 入口、就緒門控、設定檔 `SongRequestMod.toml`、日誌 |
| `SelectDriver.cs` | 點歌跳轉 |
| `SongTable.cs` | 曲庫讀取與 JSON |
| `Web.cs` | HttpListener、API、SSE |
| `MainThread.cs` | 主執行緒排程、背景執行緒、效能計時 |
| `Jackets.cs` / `LiveState.cs` | 封面 / 正在遊玩 |
| `Tunnel.cs` / `Direct.cs` | Cloudflare / IPv6、NAT 打洞、UPnP |
| `Aliases.cs` / `CrashGuard.cs` | 別名庫 / 崩潰保護（預設關） |
