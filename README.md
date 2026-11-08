# mai2_research

maimai DX（`Sinmai.exe`）的 MelonLoader mod 研究筆記：遊戲環境、怎麼接進遊戲、遊戲內部結構、音效系統，以及實際做 mod 時踩過的坑。

內容來自開發 [maimai-song-request-](https://github.com/chidi0716/maimai-song-request-)（點歌台 mod）的過程，以及幾個參考專題的反編譯分析。

> 本 repo 只放筆記與自己寫的工具，**不放任何遊戲檔案**（DLL、音效、圖片）。遊戲素材請自行從合法取得的遊戲中讀取。

## 目錄

> 給 AI 讀：[`AI_CONTEXT.md`](AI_CONTEXT.md) 是全部內容的單檔濃縮版（條列、保留所有類別 / 方法名稱），丟給 AI 當背景資料用這份就好。

| 文件 | 內容 |
|---|---|
| [01 環境與 MelonLoader](docs/01-環境與MelonLoader.md) | 遊戲與 MelonLoader 版本、mod 專案設定、生命週期、除錯方式 |
| [02 接入遊戲的方法](docs/02-接入方法.md) | Harmony 補丁、讀寫私有成員、管理器、協程、輸入、額外資源 |
| [03 遊戲內部結構](docs/03-遊戲內部結構.md) | Process / Monitor 架構、選曲畫面、曲目與譜面資料、DX/STD |
| [04 音效系統（CRI ADX2）](docs/04-音效系統.md) | ACB/AWB 格式、音效表、ADX/HCA 解密、替換與轉向音效 |
| [05 踩坑紀錄](docs/05-踩坑紀錄.md) | 撞名、執行緒、初始化時機、其他 mod 干擾、版本差異… |
| [06 參考專題](docs/06-參考專題.md) | 點歌 mod 原作、扫码点歌、冰冰冰正解音、DxPassCompat、MaiL2d、murasame 角色包、maimai-dghub-link、NGO 銘牌包、maimai-ngo |
| [07 SongRequest 架構](docs/07-SongRequest架構.md) | 點歌台 mod 的運作邏輯、API、遠端分享 |
| [08 加入自訂內容](docs/08-加入自訂內容.md) | 自訂 ID、資料表注入、不上傳伺服器、AssetBundle / 語音 / 圖片、伙伴動畫、DX PASS |
| [09 遊戲流程與狀態讀取](docs/09-遊戲流程與狀態讀取.md) | 全部畫面（Process）一覽、即時判定入口、譜面與進度、成績、倒數計時、版本與玩家名稱、按鈕 LED、自動播放、選項表 |
| [10 資源與選項包](docs/10-資源與選項包.md) | StreamingAssets 選項包（`A???`）、收藏品 XML 與自動解鎖、貼圖載入、動態銘牌、改 `resources.assets` 換皮、執行期換圖入口 |
| [11 效能與測試](docs/11-效能與測試.md) | 遊戲的 GC 時機、Mono Boehm GC 與洩漏、量測方式、機台按鍵與模擬、測試注意事項 |
| [12 玩法與系統](docs/12-玩法與系統.md) | 音符與判定、分數 / 達成率 / DX 分數公式、評級與 Rating（B35 + B15）、一次遊玩流程、地圖 / 夥伴 / 段位 / 對戰等長期系統 |
| [tools/cri](tools/cri/README.md) | 解析 ACB、解密 ADX、解碼 HCA、產生音效試聽頁的工具 |

## 快速重點

- `Sinmai.exe` 是 **Unity + Mono（x64）**，遊戲邏輯在 `Sinmai_Data\Managed\Assembly-CSharp.dll`，可以用 ILSpy 直接反編譯閱讀。
- 用 **MelonLoader 0.6.x（Mono 版）** 載入 mod，主要用 **Harmony** 掛補丁接入遊戲。
- 碰 Unity / 遊戲物件**只能在主執行緒**（`OnUpdate`）；**遊戲資料載入完**（`DataManager.IsLoaded()`）之前不要碰遊戲物件。
- 音效是 CRI ADX2，`Mai2Cue` 有 488 個音效；ADX（第 9 型加密）與 HCA 都用金鑰 `7F4551499DF55E68`（vgmstream 公開金鑰清單）。
