# AI_CONTEXT：maimai DX（Sinmai.exe）MelonLoader mod 知識濃縮

> 給 AI 一次讀完用的單檔摘要。詳細說明與範例在 `docs/01`～`09`，工具在 `tools/cri/`。
> 名稱來自反編譯 `Assembly-CSharp.dll`（約 1.65～1.70 版），不同版本可能不同；不確定時先反編譯確認。
> 規則：不要把遊戲檔案（DLL、音效、圖片）放進公開 repo。

## 1. 環境

- `Package\Sinmai.exe`：Unity **2018.4.7f1**、**Mono**（不是 IL2CPP）、x64。
- 遊戲邏輯：`Package\Sinmai_Data\Managed\Assembly-CSharp.dll`，可用 ILSpy / `ilspycmd -p -o out -r Managed -r MelonLoader/net35 Assembly-CSharp.dll` 反編譯。
- 版本代號：SDEZ = 日版（1.60／1.65／1.66／1.70），SDGB = 國服（1.50／1.55，版本字串如 `Ver.CN1.56-B`）。部分 SDEZ 1.66 包體要先啟動外置 AMDaemon（`Plugins\amdaemon_api.dll` 和 `Managed\AMDaemon.NET.dll` 必須同一套）。
- Loader：MelonLoader **0.6.4 Mono**，內含 HarmonyX（`MelonLoader\net35\0Harmony.dll`）。
- 目錄：`Mods\*.dll`（mod）、`UserData\MelonPreferences.cfg`（`MelonPreferences`）、`MelonLoader\Latest.log`（日誌）、`LocalAssets\`（mod 慣用的本機資源）、`Sinmai_Data\Plugins\`（原生 DLL）。
- csproj：`net48`、`LangVersion 9`、`Microsoft.NETFramework.ReferenceAssemblies`；參考 `MelonLoader.dll`、`0Harmony.dll`、`Assembly-CSharp.dll`、`UnityEngine.CoreModule.dll`（+ 依需要 `InputLegacyModule`、`ImageConversionModule`、`AssetBundleModule`、`UnityEngine.UI`），全部 `Private=false`。Linux 上 `dotnet build` 也能編。
- 骨架：`[assembly: MelonInfo(typeof(Mod), name, ver, author)]`、`[assembly: MelonGame("sega-interactive", "Sinmai")]`；`MelonMod` 的 `OnInitializeMelon`（設定、Harmony）、`OnLateInitializeMelon`（起伺服器等）、`OnUpdate`（主執行緒每幀）、`OnApplicationQuit`。
- 資源可用 `EmbeddedResource` 內嵌進 DLL。

## 2. 接入方式

- **Harmony**（主要）：MelonLoader 自動套用組件內所有 `[HarmonyPatch]`。自己控制：`[assembly: HarmonyDontPatchAll]` + `HarmonyInstance.PatchAll(typeof(X))`；`new HarmonyLib.Harmony(id).PatchAll(asm)`；`harmony.Patch(method, prefix, postfix, transpiler, finalizer)`（可依設定決定掛不掛）。
- 跨版本容錯：`AccessTools.TypeByName("Process.X")` + `AccessTools.Method` + `harmony.Patch`，找不到就略過；不要用 `[HarmonyPatch(typeof(X))]` 寫死可能不存在的型別。Postfix 的 `__instance` 宣告成 `object`，同一個 Postfix 就能掛在多個 Process 上。原方法參數可以用同名或位置 `__0`、`__1` 注入。
- 補丁類型：Prefix（回 `false` 略過原方法；改參數 / `ref __result`）、Postfix（讀 / 改結果）、Finalizer（`Exception __exception`，回 `null` 吞掉例外）、Transpiler（改 IL，少用）。
- 指定目標：`[HarmonyPatch(typeof(X), "M", typeof(int))]` 指定多載；getter 用 `MethodType.Getter` 或 `"get_Prop"`。
- 讀寫私有成員：
  - 參數注入：`__instance`、`___欄位名`。欄位本身以 `_` 開頭時是**四個底線**，例如 `____combineMusicDataList`。
  - `AccessTools.FieldRefAccess<T, F>("_field")`：最快、有型別。
  - `AccessTools.MethodDelegate<Action<T, A>>(AccessTools.Method(typeof(T), "Priv"))`：呼叫私有方法。
  - `Traverse.Create(obj).Field("_x").GetValue<T>()`：最短，速度接近反射。
  - 一般反射。
- **執行緒**：碰 Unity / 遊戲物件只能在主執行緒（`OnUpdate`）。`Application.dataPath`、`FindObjectOfType`、`Time` 也算。外部執行緒只排隊。
- **就緒門控**：`Singleton<Manager.DataManager>.Instance.IsLoaded()` 之前不要碰遊戲物件。否則可能登入時閃退（`PlInformationProcess.RestoreGhost` 空參考）。
- **協程**：借遊戲的 `MonoBehaviour`（例如某個 Monitor）呼叫 `StartCoroutine`；`yield return null` 等一幀。
- **輸入**：`UnityEngine.Input.GetKeyDown(KeyCode.F8)`（需參考 `InputLegacyModule`）；機台按鈕走遊戲 `InputManager`（`ButtonSetting.Button04`…）。

## 3. 遊戲結構

### 3.1 Process / Monitor

- 流程由 Process 組成（`MusicSelectProcess`、`PlInformationProcess`、`CodeReadProcess`…），命名空間是全域的 `Process`。
- 每個玩家一個 Monitor（`MusicSelectMonitor`…，命名空間 `Monitor`）。
- `MusicSelectProcess.OnStart` / `OnRelease` 會**按玩家數各觸發一次**，記得去重。
- Process 一覽（`OnStart` / `OnRelease` Postfix 可得知目前畫面）：
  - `Process.AdvertiseProcess`、`Process.AdvertiseCommercial.AdvertiseCommercialProcess`（待機）
  - `Process.EntryProcess`（登入）
  - `Process.PlInformationProcess`、`Process.InformationProcess`（資訊）
  - `Process.GetPresentProcess`（禮物）
  - `Process.ModeSelect.ModeSelectProcess`（模式選擇）
  - `Process.RegionalSelectProcess`（地圖）
  - `Process.CharacterSelectProces`（角色選擇；**原名少一個 s**）
  - `Process.TicketSelect.TicketSelectProcess`（功能票）
  - `Process.MusicSelectProcess`（選曲）
  - `Process.MusicSelectInfoProcess`、`Process.GetMusicProcess`（讀取）
  - 打歌中：用 `GameManager.IsInGame` 判斷
  - `Process.ResultProcess`（結算）
  - `Process.CodeReadProcess`（DX PASS）
- `OnRelease` 只在 `ReferenceEquals(記住的, __instance)` 時才清除。

### 3.2 `MusicSelectProcess`

- SubSequence：0 Music、1 Genre、2 SortSetting、3 Difficulty、4 UtageDifficulty、5 Menu、6 Option、7 Character。
- 成員：
  - `CombineMusicDataList`（`List<ReadOnlyCollection<CombineMusicSelectData>>`，[分類][卡]）
  - `CurrentCategorySelect`、`CurrentMusicSelect`
  - `ScoreType`（0 STD、1 DX）
  - `CurrentDifficulty[p]`、`DifficultySelectIndex[p]`
  - `ChangeBGM()`、`CalcMonitorDifficulty(bool)`（**會覆寫難度，先呼叫再設難度**）
  - 私有 `SyncNext(SubSequence)`（所有玩家一起切子畫面，並記住前一個）
  - `SetInputLockInfo(p, ms)`、`IsInputLocking(p)`
  - `IsUtageMusicFolder()`、`IsGhostFolder(p)`、`IsConnectionFolder()`、`IsChallengeFolder()`、`IsTournamentFolder()`、`IsExtraFolder(p)`
- 私有欄位：`_subSequenceArray`（`SequenceBase[][]`）、`_currentPlayerSubSequence`、`_beforePlayerSubSequence`、`_mainSequence`、`_combineMusicDataList`。
- 遊戲自己的確認選曲流程：`monitor.ChangeButtonImage(Button04, 14)` → `SetScrollMusicCard(false)` → `OutGenreTab()` → `SetInputLockInfo(p, 1200f)` → `SyncNext(Difficulty 或 UtageDifficulty)`。

### 3.3 `CombineMusicSelectData`

- `msDetailData.musicId`
- `musicSelectData[0|1].MusicData`（STD / DX）
- `existStandardScore`、`existDeluxeScore`
- `isExistsScore`（1.70 是 `List<bool>`）
- `isRandomScore`

### 3.4 資料

- `DataManager`：
  - 公開的 `GetMusics()` / `GetMusic(id)` 常被其他 mod（AquaMai、MuNET）改寫，結果可能不完整。要全量時讀私有 `_musics` 或選曲列表。
  - 載入前的內部表是非 null 的空佔位表（`CreateDummyTable`）。
  - 其他方法：`GetMusicGenre`、`GetUdemaeBoss`（可能回 null 導致閃退）、`GetPartners()`（`Safe.ReadonlySortedDictionary<int, PartnerData>`）。
- `MusicData`：`GetID()`、`name.str`、`artistName.str`、`genreName`、`bpm`、`AddVersion.str`、`notesData`、`IsDisable()` / `disable`、`jacketFile`、`thumbnailName`。
- `Notes`：
  - 欄位：`isEnable`、`level`、`levelDecimal`（**定數 = level + levelDecimal/10**）、`notesDesigner.str`。
  - 難度看 `notesData` 的**位置**（0 BASIC～4 Re:MASTER），不要看 `notesType`。
- DX / STD：
  - 一首歌一張卡，用 `ScoreType` 切換 DX / STD。
  - DX 的 ID 通常是 STD + 10000，有例外（Trust 695 / 11726），找不到時用曲名比對。
  - 要依使用者點的是哪一套決定 `ScoreType`。
- 其他：
  - `GameManager`（靜態）：`SelectMusicID`、`SelectDifficultyID[]`、`CurrentDifficulty[]`、`IsInGame`、`MusicTrackNumber`（第幾首，可用來偵測換歌）
  - `Notes.musicLevelID` → `DataManager.GetMusicLevel(id).levelNum`：顯示用等級（例如 `13+`）
  - 宴會場判斷：`genreName.id == 107`；或 ID `>= 100000` 且 `utageKanjiName` 不是空的（或曲名以 `[` 開頭）。譜面在 `notesData[0]`，難度值 5
  - `Singleton<UserDataManager>.Instance.GetUserData(i).IsEntry`
  - `AssetManager.Instance().GetJacketTexture2D(name)` / `GetJacketThumbTexture2D(name)`：用資源名呼叫，int 版本會走被改寫的 `GetMusic`。
  - 圖片輸出：遊戲貼圖不可讀，要用 `RenderTexture` + `ReadPixels` + `EncodeToPNG`，全部在主執行緒做。

### 3.5 即時狀態（打歌 / 結算 / 計時）

- **判定**：Postfix `JudgeResultSt.UpdateScore(int monitorIndex, NoteScore.EScoreType type, NoteJudge.ETiming timing)` → `NoteJudge.ConvertJudge(timing)` 回傳 `NoteJudge.JudgeBox`（Critical / Perfect / Great / Good / Miss）。每個音符都會經過，在主執行緒執行。
- **譜面**：`NotesManager.Instance(player).GetSessionInfo()`（`musicId`、`difficulty` 0～4 = BASIC～Re:MASTER、5 = 宴會場、`notesData`）。
- **進度**：靜態 `NotesManager.GetCurrentMsec()`、實例的 `getPlayFirstMsec()` / `getPlayFinalMsec()`（小寫 g）。
- **分數**：`GamePlayManager.Instance.GetGameScore(player, -1)` → `GameScoreList`：`CriticalNum`、`PerfectNum`、`GreatNum`、`GoodNum`、`MissNum`、`Combo`、`MaxCombo`、`DxScore`、`IsEnable`（false = 該側沒在玩）、`SessionInfo`、`GetAchivement()`（原名拼錯）。
- **結算**：`ResultProcess` 的私有欄位 `_gameScoreLists[p]`、`_userScores[p]`（`deluxscore`）、`_musicID`。`OnStart` 當下資料可能還沒填好，要之後幾幀重讀。
- **畫面倒數**：`process.container.processManager._genericManager._timerController[0]` 的 `CountDownSecond`、`IsInfinity`。找不到時改找 `_timer`、`Monitors[0]`、`Context.GetCurrentState()`。
- **版本**：`MAI2System.SystemConfig.Instance.config.displayVersionString`；備用 `config.romVersionInfo.versionNo.versionString`、`Manager.AmManager.Instance.VersionNo.versionString`。
- **玩家**：`UserDataManager.GetUserData(i)` 的 `IsEntry`、`Detail.userName`；`Manager.NetDataManager.Instance.GetNetUserData(i)`。空字串、`GUEST`、「游客」都視為沒有名稱（先做 NFKC 正規化）。
- **寫法**：
  - 多個候選成員名稱、反射結果快取（`MethodInfo` 與整數索引器 `Item(int)`）。
  - 非打歌畫面每 250～1000 毫秒讀一次。
  - 用 `Stopwatch` 量慢路徑。
  - 具名 `Semaphore` 防止重複載入。

## 4. 音效（CRI ADX2）

### 4.1 格式

- `.acb`：`@UTF` 表，可能內嵌 memory AWB（`AwbFile`）。`StreamAwbHash` 是配對 `.awb` 的 MD5。
- `.awb`：AFS2。`0x05` 位移欄寬、`0x06` ID 欄寬、`0x08` 數量、`0x0c` 對齊、`0x0e` subkey。

### 4.2 Cue 解析鏈

- `CueTable.ReferenceType`：1 = Waveform、2 = Synth（`ReferenceItems` 是 `(u16 type, u16 idx)`）、3 = Sequence（`TrackIndex` → `TrackTable.EventIndex` → `TrackEventTable.Command`，code 2000 / 2003 的參數是 `(type, idx)`）。
- `WaveformTable`：`Streaming` 0 = memory、1 / 2 = stream；`MemoryAwbId` / `StreamAwbId`；`EncodeType` 0 = ADX、2 = HCA。

### 4.3 `Mai2Cue`

- 遊戲主要音效庫，`AcbID` 0。
- 488 個 cue，ID 0～543（不連續）。
- 前綴：`SE_GAME` 212、`SE_RESULT` 46、`SE_MAP` 37、`SE_KALEID` 33、`SE_EMONEY` 20、`SE_ENTRY` 15、`SE_SYS` 12、`BGM_*` 13、`JINGLE_*` 16。
- 正解音 `SE_GAME_ANSWER` = CueId 88。
- 歌曲與角色語音不在 `Mai2Cue`。

### 4.4 加密

- 金鑰 **`7F4551499DF55E68`**（vgmstream 公開金鑰），ADX 與 HCA 共用，subkey 0。
- ADX 第 9 型（標頭 `0x12-0x13` = `04 09`）：
  - 金鑰流：`k = key - 1`；`x = (k>>27)&0x7fff`；`mul = ((k>>12)&0x7ffc)|1`；`add = ((k<<1)&0x7fff)|1`。
  - 每個音框的 scale：`(scale ^ x) & 0x1fff`，然後 `x = (x*mul + add) & 0x7fff`。
  - 最後把 `0x13` 改成 0，再用 `ffmpeg -f adx` 解碼。
- HCA：magic `C8 C3 C1 00`（加了遮罩的 `HCA\0`），用 vgmstream `clHCA` 加金鑰解碼。

### 4.5 在 mod 裡換音效（AnswerSoundSwitch 的做法）

1. `Singleton<SoundCtrl>.Instance.LoadCueSheet(6, 路徑不含副檔名)`。
2. 反射私有 `GetCueSheet(6)` → `CriAtomExAcb.GetCueInfo(name, out info)`，確認 ID 對得上。
3. Prefix `SoundCtrl.Play(PlaySetting)`：`AcbID == 0 && CueIndex == 88` 時改成 `AcbID = 6`。
4. Postfix `CriAtomExPlayer.SetCue` → `SetVolume(1.5f)`。

改成一張對照表，就能替換任意多個音效，而且不動遊戲原檔。

## 5. 自訂內容（MaiL2d / DxPassCompat 的做法）

- **自訂 ID**：MaiL2d 用負數（第 i 個 = `-1-i`），DxPassCompat 用 `9000000+i`。取資料方法加 Prefix：自訂 ID 回自己的資料並 `return false`，否則 `return true`。
- **注入資料表**：
  - Postfix `DataManager.GetPartners`：複製原表，加入 `new PartnerData().Init(Serialize.PartnerData{ name = StringID{id,str}, naviChara, priority })`，結果快取。
  - Prefix `CollectionData.IsHave` getter：自訂 ID 回 true。
  - DxPassCompat：用反射逐一複製 `CardTypeData` 的屬性（呼叫私有 setter）。
- **不上傳伺服器**：
  - Postfix `VOExtensions.Export(Net.VO.Mai2.UserDetail, ulong)`（伺服器 → 本機）：換成本機選的自訂 ID。
  - Postfix `Export(Manager.UserDatas.UserDetail)`（本機 → 伺服器）：還原成伺服器原本的 ID。
  - 本機選擇存在 `PlayerPrefs`（`MaiL2DUserModel:{userId}`）。
- **資源**：
  - AssetBundle：Unity 2018.4.7f1 / StandaloneWindows64。`AssetBundle.LoadFromFile` → `LoadAsset<GameObject>("L2dNaviCharaRoot")`；內嵌的用 `LoadFromStream(GetManifestResourceStream)`。
  - 原生 DLL：第一次啟動時寫到 `Sinmai_Data\Plugins`。
  - 圖片：`Texture2D.LoadImage` → `Sprite.Create`。
- **伙伴**：
  - Prefix `AssetManager.GetNaviCharaPrefab(id)` / `GetPartnerTexture2D(id)`。
  - 語音：`SoundManager.GetPartnerVoiceCueName(voiceID)` 回傳 ACB 路徑。官方伙伴語音 ACB 有 92 個 cue（`VO_000080`～`VO_000254`），HCA；用 ACE 編輯，只刪 Track、不要刪 Cue。
  - 結算畫面的 `NavigationCharacter`（由 `ResultMonitor` 管理）。Animator 狀態：`Navi_Fun_Loop_02`（Clear）、`Navi_Fun_Start`（被觸摸）、`Navi_Sad_01`（未 Clear）。
  - MaiL2d 另外提供參數 `IsClear`（Postfix `ResultMonitor.SetStartData`）、`Random`（Prefix `TouchPartnerCharacter`）。
- **DX PASS**：
  - `CodeReadProcess`（`GetUserCard`、`GetEnableUserCard`、`GetReadCard`、`GetCardTypeData`、`IsValidCard`、`IsInPeriod`）、`CodeReadMonitor.Scroll`、`ReadCardChainList.Deploy`（私有 `_readCardChainList`）。
  - `CardData.IsDisable` / `enableVersion`（舊卡不顯示 → 把 `StringID.id` 改成 12）、`UserData.CardList`。
  - 卡種：2 Bronze、3 Silver、4 Gold、5 Platinum、6 Freedom。

## 6. 踩坑（症狀 → 解法）

- **撞名**：
  - 遊戲有全域命名空間 `Process`、`Monitor`。用 `using Proc = System.Diagnostics.Process`、`global::Process.X`、`System.Threading.Monitor`。
  - `HarmonyLib.Harmony`、`System.Type` 寫完整。
- **非主執行緒碰 Unity** → 偶發閃退。外部執行緒只排隊。
- **太早碰遊戲物件** → 登入閃退。用就緒門控。
- **曲目變少** → 被其他 mod 過濾或讀到佔位表。多路讀取取最多；整庫被判停用時關掉停用過濾。
- **Finalizer 吞例外** → 遊戲帶著錯誤狀態繼續跑。預設關閉。
- **主執行緒直接寫網路** → 卡死。每個連線一條背景寫入執行緒，加逾時；不要用 ThreadPool（HttpListener 也靠它）。
- **卡頓**：
  - 原因：整表重掃、JSON 重建、封面編碼擠在同一幀。
  - 解法：便宜的變化偵測、片段快取、跳轉時暫停重活。
- **DX 譜點錯**：依使用者點的那套決定 `ScoreType`。
- **在難度畫面再跳一次後返回失效**：先 `SyncNext(Music)` 退回。
- **`CalcMonitorDifficulty` 覆寫難度**：先呼叫它再設難度。
- **`isExistsScore` 型別**：可能是 `bool[]`、`List<bool>` 或 `IList`，都要支援。
- **Mono `HttpListener`**：
  - 會比對 Host 標頭，外部網域要改寫 Host。
  - 不支援 IPv6，要用 `TcpListener` 接再轉給它。
- **`ServicePointManager`** 是整個程序共用的，網路下載交給外部程式。
- **跨版本**：關鍵成員用反射加防呆，找不到就停用該功能；或用 SHA-256 標明支援的 DLL 版本。
- **ADX 解出雜訊**：漏了 `& 0x1fff`。
- **遊戲原本的拼錯**：`CharacterSelectProces`、`GetAchivement`、`deluxscore`、`getPlayFirstMsec`。照遊戲的拼法寫，不確定時兩種都試。

## 7. SongRequest（chidi0716/maimai-song-request-，v1.1.11）

- **功能**：`http://127.0.0.1:8790/` 網頁點歌 → 遊戲跳到該曲難度畫面。另有正在遊玩面板（SSE）、遠端分享。
- **接入**：
  - Postfix `MusicSelectProcess.OnStart` / `OnRelease`。
  - `FieldRefAccess` 讀子畫面欄位，`MethodDelegate` 呼叫 `SyncNext`。
  - `OnUpdate` 每幀最多處理 4 件排隊的工作。
- **跳轉流程**：
  1. 檢查狀態與輸入鎖。
  2. 在列表裡找卡。
  3. 必要時退回選曲列表。
  4. 依序設分類 / 曲目 / `ScoreType` → `ChangeBGM` → `CalcMonitorDifficulty(true)` → 設難度。
  5. 照遊戲的確認選曲流程，下一幀 `SyncNext`。
- **API**：`/api/songs`、`POST /api/play`（`id`、`diff`、`type=dx|std`）、`/api/random`、`/api/status`、`/api/npstream`、`/jacket?id=`、`/api/perf`、`/api/selfcheck`。
- **遠端分享**：
  - Cloudflare quick tunnel（`cloudflared`）。
  - IPv6 直連。
  - IPv4 直連：TCP STUN、保活、雙 STUN 比對排除對稱型 NAT、UPnP 通訊埠轉發。
  - 遠端請求要帶隨機金鑰 `?k=`（之後存 cookie），直連請求加上 `X-SongRequest-Remote` 標記。
- **設定**：`SongRequestMod.toml`。
- **原始碼**：`Mod`、`SelectDriver`、`SongTable`、`Web`、`MainThread`、`Jackets`、`LiveState`、`Tunnel`、`Direct`、`Aliases`、`CrashGuard`。

## 8. 參考專題

| 專題 | 作者 / 授權 | 重點 |
|---|---|---|
| maimai-song-request- | ZCM-X / MIT | 點歌原作；就緒門控、崩潰保護、DX 修正、效能 |
| 扫码点歌 SongSearch v1.1.1 | Clansty / 未標授權（只參考做法） | 參數注入、`levelDecimal`；反例：網頁執行緒直接操作遊戲 |
| AnswerSoundSwitch v1.1.0 | Hematemesis-V | `SoundCtrl.Play` 轉向第 6 號音效庫 |
| DxPassCompat v2.4.0（說明檔標 v2.5） | ZCM-X | DX PASS 卡面、`9000000+` ID、`Traverse` |
| MaiL2d v1.3.0 | Clansty / GPLv3 | Live2D 伙伴、負數 ID、`VOExtensions.Export`、AssetBundle、原生 DLL |
| maimai-dghub-link v1.4.10 | XiaoLan9999 / GPLv3（只參考做法） | 判定入口、Process 一覽、倒數、版本、跨版本反射；沒有新的接入技術 |
| murasame | 第三方 | MaiL2d 模型包 + 語音包（92 cue，47 個有聲音，HCA） |
| AquaMai、MuNET、ComboWeb | — | 只被提到；前兩者會改寫曲目讀取 |
