# 14 AquaMai 功能與遊戲入口

> 來源：[MewoLab/AquaMai](https://github.com/MewoLab/AquaMai)（Apache-2.0，commit `77f6eb1`，2026-10-31）。只讀了原始碼，沒有執行。
>
> - `AquaMai.Mods` 共 139 個設定段（`[ConfigSection]`），每段都是「一個功能 + 它掛的遊戲方法」。
> - 下面的入口是用腳本從 `[HarmonyPatch(typeof(X), "M")]` 抽出來的，只列寫 mod 時最有參考價值的。
> - 「預設」= `defaultOn: true`，沒寫的要在 `AquaMai.toml` 自己打開。

## 1. 跟本知識庫直接相關的發現

- **`N???` 為什麼放在 StreamingAssets 也能讀**：`GameSystem/OptionLoadFix`（預設開）
  - Prefix `AppImage.OptionMountRootPath` getter，回傳 `Application.streamingAssetsPath`（或自訂路徑）。
  - Postfix `DataManager.GetDirs` 去掉重複的資料夾。
  - 本機 `StreamingAssets\N100`、`N999` 會被讀到，靠的就是它。原版的掛載路徑是 AMDaemon 提供的，沒有在 `Assembly-CSharp` 裡確認。
- **`GetMusics()` 結果變少**（[05](05-踩坑紀錄.md) 第 6 條）的一個來源是 `UX/HideSelfMadeCharts`：
  - Postfix `DataManager.GetMusics`，用 `StackTrace` 確認呼叫者是 `MusicSelectProcess` 才過濾。
  - 「官方」選項包的判斷：資料夾裡有 `DataConfig.xml` 或 `OfficialChartsMark.txt`；其他包裡的歌都算自製譜。
- **按鈕 LED 在 Maimoller 上會不會亮**：`GameSystem/MaimollerIO`
  - Prefix `Bd15070_4IF._setColor`、`_setColorMulti`、`_setColorFet`、`_setLedAllOff` 等，把遊戲的 LED 指令轉成 Maimoller 的 HID 指令（`Led1p` / `Led2p` 預設 true）。
  - 所以 mod 呼叫 `MechaManager.LedIf[p].SetColor(...)` 在 Maimoller 上應該會亮（原始碼推斷，沒實測）。本機 `AquaMai.toml` 已開 `[GameSystem.MaimollerIO]`。
  - 亮度：`Tweaks/LedBrightnessControl` 也掛同一組 `_setColor*`。
- **直讀圖片 / PV**：見 [13](13-自製譜與選項包管理.md)。

## 2. 寫 mod 可以借用的技巧

| 技巧 | 來源功能 | 做法 |
|---|---|---|
| **擴充遊戲內建的列舉表** | `GameSystem/SongConstantSort`（定數排序） | 遊戲的選項 / 分頁是 `DB.XxxID` enum + `XxxIDEnum` 靜態表。Prefix `SortTabIDEnum` 的 `GetEnd`、`IsValid`、`GetName`、`GetDetail`、`GetFilePath`、`GetEnumName`、`GetEnumValue`，讓新值（`End` 之後）合法；再改 `MusicSelectProcess.AddSort` / `CategoryTabSort` 和 `MusicSelectMonitor` 的分頁圖 / 顏色 / 字串 |
| **不讓自訂值上傳** | 同上 | Postfix `VOExtensions.Export(UserExtend)`，上傳前把 `sortCategorySetting` 的自訂值換回 `Genre`。和 [08](08-加入自訂內容.md) MaiL2d 的做法相同 |
| **跨版本欄位名** | 同上 | `GameInfo.GameVersion >= 26500` 時用 `_beforeCategorySortSetting`，否則用 `_categorySortSetting`（遊戲版本號 ≥ 26500 時欄位改名；1.70 反編譯確認有 `_beforeCategorySortSetting`） |
| **取得精確判定誤差** | `Utils/UnstableRate`、`UX/JudgeAccuracyInfo` | Postfix `NoteBase.Judge`、`HoldNote.JudgeHoldHead`，讀私有欄位 `___JudgeTimingDiffMsec`；扣掉玩家的判定調整 `UserOption.GetJudgeTimingFrame() × 16.6667ms`。Slide 用 `SlideRoot.Judge` |
| **暫停 / 跳轉 / 變速** | `UX/PracticeMode`、`Fix/DebugFeature` | 1.70 的 `GameProcess` 沒有 `debugFeature` 欄位，AquaMai 用自己的 polyfill：改計時器（`NotesManager.UpdateTimer`）、影片 `MovieController.Pause` / `SetSeekFrame`、音訊播放器變速；目前時間 = `NotesManager.GetCurrentMsec() - 91`；跳轉後 `GameCtrl.ForceNoteCollect` 收掉已過的音符 |
| **全場景換圖** | `Fancy/ResourcesOverride`（標「危險功能」） | Postfix `Graphic.Rebuild`、`CanvasScaler.OnEnable`，依 `sprite.name` / `texture.name` 查自己的圖替換。缺點是每次重建都會跑，見 [11](11-效能與測試.md) 的 `Object.name` 配置問題 |
| **條件式掛補丁** | 多數功能 | `[EnableIf(nameof(條件))]`、`OnBeforePatch(Harmony)` 依版本或設定決定掛哪一組（AquaMai 自己的框架） |
| **判斷呼叫者** | `UX/HideSelfMadeCharts` | Postfix 裡用 `new StackTrace().GetFrames()` 看是不是某個類別呼叫的，只在特定畫面改結果 |

## 3. 功能目錄（依類別，節錄）

### GameSystem（遊戲系統）

| 功能 | 預設 | 入口 |
|---|---|---|
| `LoadLocalImages` 直讀圖片 | ✔ | `DataManager.LoadMusicBase`、`AssetManager.Get*Texture2D(string)`、`MusicSelectMonitor.Initialize` |
| `MovieLoader` 直讀 PV | ✔ | `GameCtrl.Initialize`、`GameMonitor.SetMovieMaterial`、`MovieController.*`、`Player.SetSpeed` |
| `LoadAssetBundleWithoutManifest` | ✔ | `AssetBundleManifest.GetAllAssetBundles`、`OptionDataManager.CheckAssetBundle` |
| `AssetBundleManager`（忽略載入失敗的 .ab） | ✔ | `AssetBundleManager.OnSucess`（原名拼錯） |
| `Fonts` 自訂字型（補中文字形） | ✔ | `TextMeshProUGUI.Awake` |
| `OptionLoadFix` | ✔ | `AppImage.OptionMountRootPath`、`DataManager.GetDirs` |
| `KeyMap` 按鍵映射 | ✔ | `DB.JvsButtonTableRecord`、`SwitchInput.IsOn/HasOnNow` |
| `MaimollerIO`、`AdxHidInput` | — / ✔ | `Bd15070_4IF._setColor*`、`InputManager.SetNewTouchPanel`、`GameMain.Update` |
| `TouchToButtonInput`、`TouchAreaRemapper` | | `InputManager.GetButtonDown/Push/LongPush`、`InputManager.SetNewTouchPanel` |
| `QuickRetry`（3456 重開） | | `Monitor.QuickRetry.Execute/IsQuickRetryEnable` |
| `SinglePlayer` 單人模式 | | `EntryMonitor.DecideEntry`、`PleaseWaitProcess.OnStart`、`WaitPartner.Open` |
| `SongConstantSort` 定數排序 | | 見第 2 節 |
| `Unlock` 全解 | | `EventManager.IsOpenEvent`、`MapMaster.IsLock`、`CourseData.isLock`、`MusicData.IsDisable`、`UserData.AddCollections`、`TicketData.maxCount` |
| `DisableTimeout` 去倒數 | | `TimerController.PrepareTimer/UpdateTimer`、`CommonTimer.SetVisible`、各 Process 的 `OnStart` |
| `EnableFreedomMode`（SDGA） | | `ModeSelectMonitor.Initialize` |
| `RemoveEncryption` | ✔ | `Packet.Obfuscator`、`Net.CipherAES`（`TypeByName`） |
| `StartupDirectToGame`（`--music`） | ✔ | `StartupProcess.OnUpdate`、`GameProcess.OnStart` |
| `Sound`、`SoundRouting`、耳機音量 | | `WasapiExclusive.Intialize`、`CriAtomEx.RegisterAcf`、`CriAtomExPlayer.SetAisacControl` |

### UX / Utils（體驗、工具）

| 功能 | 預設 | 入口 |
|---|---|---|
| `ImmediateSave` 打一首存一首 | ✔ | `GameProcess.OnStart/OnRelease`、`ResultProcess.OnStart` |
| `OneKeyEntryEnd`、`OneKeyRetrySkip`、`QuickEndPlay` | | `GameMainObject.Update`、`GameProcess.OnUpdate` |
| `PracticeMode` 練習模式 | | 見第 2 節 |
| `JudgeAccuracyInfo`、`UnstableRate` | | 見第 2 節；結算畫面 `ResultMonitor.ChangeScoreBoard` |
| `SelectionDetail` 歌曲詳情 | | `MusicSelectMonitor.SetRivalScore/UpdateRivalScore` |
| `HideSelfMadeCharts` | | `DataManager.GetMusics` |
| `Hide1879`（隱藏 Xaleid◆scopiX） | ✔ | `NotesListManager.CreateNormalNotesList` |
| `GrantFinalGateKey`（Enter 拿 KLD 鑰匙） | ✔ | `KaleidxScopeProcess.OnStart/OnUpdate` |
| `FestaControl` | | `FestaManager.CanAttendFesta/Initalize` |
| `DisableLightOutGame`、`LedOffOnQuit` | | `Bd15070_4IF.SetColor*`、`GameMain.OnApplicationQuit` |
| `DisplayTouchInGame` 觸控顯示 | | `InputManager.RegisterMouseTouchPanel`、`GameProcess.OnUpdate` |
| `EarlyContinue` | | `GameManager.SetMaxTrack`、`ResultProcess.ToNextProcess` |
| `ShowErrorLog` 崩潰視窗 | ✔ | `GameMain.ExceptionHandler` |
| `LogNetworkRequests`、`LogUserId` | | `Packet.Create/ProcImpl`、`PacketGetUserPreview` |
| `InstantQuit` | | `Application.Quit` |

### Fancy（外觀）

| 功能 | 入口 |
|---|---|
| `CustomSkins` 音符皮膚 | `GameNotePrefabContainer.Initialize`、`GameCtrl.Initialize`、`SlideFan.Initialize` |
| `CustomNoteTypes` 自訂音符 | `NotesReader.loadNote`、`Ma2fileRecordID.findID` |
| `ResourcesOverride` 全場景換圖 | `Graphic.Rebuild`、`CanvasScaler.OnEnable` |
| `CustomButton`、`CustomLogo`、`CustomVersionString`、`CustomPlaceName`、`CustomCreditsString` | `ButtonManager.Initialize`、`AdvertiseProcess.OnStart`、`MAI2System.Config.displayVersionString`、`ResultCardBaseController.Initialize`、`CreditController.SetCredits` |
| `CustomIntroCinematic`、`TrackCamouflage`（隱藏曲目資訊） | `MusicSelectProcess.GameStart`、`TrackStartMonitor.SetTrackStart`、`AssetManager.GetJacketTexture2D` |
| `SetFade` 轉場變種 | `FadeProcess.OnStart`、`NextTrackProcess.OnStart`、`Resources.Load` |
| `DemoMaster`、`RandomBgm`、`HideMask`、`HideHanabi` | `AdvDemoProcess.OnStart`、`SoundManager.PlayBGM`、`MonitorBackgroundTownController.Awake`、`TapCEffect.SetUpParticle` |
| `JudgeDisplay4B`、`BreakSlideJudgeBlink`、`SlideArrowAnimation` 等遊玩外觀 | `JudgeGrade.Initialize`、`SlideJudge.*`、`SlideRoot.*` |
| `Triggers`（在特定時機執行命令） | `AdvertiseProcess/EntryProcess/MusicSelectProcess.OnStart` |

### Fix / Tweaks（修正、省時間）

- **修正**：
  - `FixMissingDifficultyCrash`：`MusicSelectProcess.GameStart` 時，所選難度不存在就換一個存在的。
  - `FixLongMusicRestart`、`FixLevelDisplay`、`FixConnSlide`、`LedBoardReconnect`、`DisableReboot`（`MaintenanceTimer.*`）、`FixCheckAuth`。
- **省時間**：
  - `CheckSkip`、`SkipStartupDelays`、`EntryToMusicSelection`（`InformationProcess.OnUpdate`、`MapResultMonitor.Initialize`）
  - `ExitToSave`（`PhotoEditProcess.OnUpdate`）、`SkipGoodbyeScreen`、`SkipEventInfo`、`IWontTapOrSlideVigorously`、`SkipTrackStart`
- **其他**：`IgnoreAimeServerError`（`OperationManager.IsAliveAimeServer`）、`SkipUserVersionCheck`（`ConfirmPlay.IsValidVersion`）、`ResetTouch`、`LockFrameRate`。

## 4. 跟自己的 mod 一起用要注意

- AquaMai 已經掛了很多入口（`GameProcess.OnStart/OnUpdate`、`MusicSelectProcess.OnStart`、`AssetManager.Get*Texture2D`、`Bd15070_4IF._setColor*`…）。自己的補丁掛同一個方法時要注意順序：AquaMai 的 Prefix 回傳 `false` 時原方法不會跑（其他 Prefix 是否照跑依 HarmonyX 行為，未驗證）；用 Postfix 比較安全（NgoPlates 用 `[HarmonyPriority(0)]` 的 Postfix）。
- `GetMusics()` 會被 `HideSelfMadeCharts` 過濾（只在選曲畫面呼叫時），要全量資料請讀私有 `_musics`。
- 想做的功能先查 AquaMai 有沒有：例如「判定誤差統計」（`JudgeAccuracyInfo`）、「練習模式」、「定數排序」已經有了，可以直接開，或參考它的入口。
