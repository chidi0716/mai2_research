# 01 環境與 MelonLoader

## 遊戲

| 項目 | 內容 |
|---|---|
| 主程式 | `Package\Sinmai.exe`：Unity 遊戲，Mono 執行環境（不是 IL2CPP），x64 |
| Unity 版本 | **2018.4.7f1**（MaiL2d 的模型範本專案版本；自製 AssetBundle 要用同版編輯器，目標 StandaloneWindows64） |
| 遊戲邏輯 | `Package\Sinmai_Data\Managed\Assembly-CSharp.dll` |
| Unity 模組 | 同資料夾的 `UnityEngine.dll`、`UnityEngine.CoreModule.dll`、`UnityEngine.UI.dll`… |
| 音效資源 | CRI ADX2（`.acb` / `.awb`），見 [04 音效系統](04-音效系統.md) |

因為是 Mono，`Assembly-CSharp.dll` 是一般的 .NET 組件，可以直接用 ILSpy / `ilspycmd` 反編譯成可讀的 C#：

```bash
ilspycmd -p -o out/ \
  -r Package/Sinmai_Data/Managed \
  -r Package/MelonLoader/net35 \
  Package/Sinmai_Data/Managed/Assembly-CSharp.dll
```

### 版本代號

| 代號 | 說明 | 例 |
|---|---|---|
| SDEZ | 日版 | 1.60、1.65、1.66、1.70（1.70 = maimai でらっくす MAGiCAL，2026-09-17 上線） |
| SDGB | 國服（中國版），版本字串像 `Ver.CN1.56-B` | 1.50、1.55 |

- 主要成員（Process、`GameManager`、`GamePlayManager`、`NotesManager`、判定入口 `JudgeResultSt.UpdateScore`）在 SDGB 1.50～SDEZ 1.66 都還在，但細節欄位會變。
- 部分 SDEZ 1.66 包體用外置的 AMDaemon 執行環境：`Sinmai_Data\Plugins\amdaemon_api.dll` 和 `Sinmai_Data\Managed\AMDaemon.NET.dll` 必須是同一套；要先啟動 AMDaemon 再啟動 Sinmai（用包體附的啟動批次檔），直接點 `Sinmai.exe` 會因為沒有 IPC 對端而起不來。

> 不同遊戲版本（例如 1.65 / 1.70）的 `Assembly-CSharp.dll` 內容不同。寫 mod 時要確認用的是哪一版；有些 mod 會直接以 DLL 的 SHA-256 標明只驗證過哪個版本。

## MelonLoader

> 以下對照本機 SDEZ 1.70 的安裝、`Latest.log`、`MelonLoader\net35\MelonLoader.dll` 反編譯與附帶的 `MelonLoader.xml`（0.6.4）。

- 版本：**0.6.4 Open-Beta**（Mono 版）。內含 HarmonyX（`MelonLoader\net35\0Harmony.dll`）、MonoMod、Mono.Cecil、Tomlet（TOML）。
- 日誌開頭會印出 `Game Type: MonoBleedingEdge`、`Runtime Type: net35`、`Unity Version: 2018.4.7f1`、`Game Name: Sinmai`、`Game Developer: sega-interactive`（`MelonGame` 要填的就是這兩個）、`Game Version: 1.0`（Unity 的 `Application.version`，不是遊戲版本）。

### 安裝結構（`Package\`）

| 路徑 | 用途 |
|---|---|
| `version.dll` | MelonLoader 的代理 DLL（Unity 啟動時會載入它）。maimai-ngo 回報有機器改用 `winhttp.dll` 才有效（NGO 實測） |
| `dobby.dll` | 原生 hook 函式庫（MelonLoader 啟動用） |
| `MelonLoader\net35\` | Mono 遊戲用的 MelonLoader 本體與參考 DLL（**編譯 mod 參考這裡**） |
| `MelonLoader\net6\`、`Dependencies\Il2CppAssemblyGenerator\` | IL2CPP 遊戲用，maimai 用不到 |
| `MelonLoader\Dependencies\SupportModules\Mono.dll` | Mono 支援模組（日誌：`Support Module Loaded: ...\Mono.dll`） |
| `MelonLoader\Dependencies\CompatibilityLayers\` | 其他 mod 框架的相容層（`IPA.dll`、`EOS.dll`） |
| `MelonLoader\Latest.log`、`Logs\` | 本次日誌、歷次日誌 |
| `UserLibs\` | 共用函式庫（最先載入，給多個 mod 共用的 DLL 放這裡） |
| `Plugins\` | **MelonPlugin**（比 mod 早，能在遊戲初始化前做事）；注意不是 `Sinmai_Data\Plugins`（那是 Unity 原生 DLL） |
| `Mods\` | **MelonMod** 本體 |
| `UserData\` | `MelonPreferences.cfg`（TOML，有 mod 用 `MelonPreferences` 存設定才會產生；本機目前沒有）、各 mod 的資料（例 `UserData\MelonStartScreen`） |

其他慣例：`Package\LocalAssets\…` 是多個 mod 共用的本機資源資料夾（AquaMai 直讀圖片、MaiL2d 模型、DxPassCompat 卡圖…）；`Package\Sinmai_Data\Plugins\` 放原生 DLL（MaiL2d 的 `Live2DCubismCore.dll`）。

### 啟動順序（本機 `Latest.log`）

1. `Preferences Loaded!`
2. `Loading UserLibss from ...\UserLibs`
3. `Loading Plugins from ...\Plugins`
4. `MelonStartScreen`（開機進度畫面；`--melonloader.disablestartscreen` 可關）
5. `Loading Mods from ...\Mods`：每個 DLL 印 `Melon Assembly loaded` + **SHA256**，再印各 mod 的名稱、版本、作者（`MelonInfo`）
6. `Support Module Loaded: ...\Mono.dll`
7. 各 mod 的 `OnInitializeMelon`（例：AquaMai 印 `> Applying ...` / `> Skipping incompatible patch: ...`）

### 載入規則（反編譯 `MelonHandler`、`MelonBase`）

- 只掃 `Mods\*.dll` **最上層**（`Directory.GetFiles(path, "*.dll")`），子資料夾裡的 DLL 不會被當 mod 載入。所以 `Mods\SongRequestMod\` 這種資料夾可以拿來放資料。
- Plugin 放進 `Mods`（或反過來）會警告 `... is a MelonPlugin and cannot be loaded as a MelonMod. Make sure it's in the right folder.`。
- 排序：先依相依關係做拓撲排序，再依 `MelonPriority` **由小到大**（預設 0）。
- 自動套用 `[HarmonyPatch]`，除非組件加了 `[assembly: HarmonyDontPatchAll]`。

### 生命週期回呼（`MelonBase` / `MelonMod`，0.6.4）

| 回呼 | 時機 |
|---|---|
| `OnEarlyInitializeMelon` | 註冊後最早的時機 |
| `OnInitializeMelon` | 讀設定、掛 Harmony |
| `OnLateInitializeMelon` | 所有 mod 都初始化完之後 |
| `OnSceneWasLoaded` / `OnSceneWasInitialized` / `OnSceneWasUnloaded` | Unity 場景事件（maimai 幾乎只有一個主場景，畫面切換要看 Process，見 [09](09-遊戲流程與狀態讀取.md)） |
| `OnUpdate`、`OnLateUpdate`、`OnFixedUpdate`、`OnGUI` | 每幀；`OnGUI` 可以用 IMGUI 畫簡單除錯介面 |
| `OnPreferencesLoaded` / `OnPreferencesSaved` | 設定檔載入 / 儲存 |
| `OnApplicationQuit`、`OnDeinitializeMelon` | 結束 |

- Plugin 另外有 `OnPreInitialization`、`OnApplicationEarlyStart`、`OnPreModsLoaded`、`OnApplicationStarted`。
- 不想繼承也可以訂閱 `MelonEvents.OnUpdate`、`OnLateUpdate`、`OnGUI`、`OnSceneWasLoaded`、`OnApplicationQuit`… 等事件。
- 其他工具：`MelonCoroutines.Start(IEnumerator)` / `Stop`（不用借遊戲的 MonoBehaviour 就能跑協程）、`LoggerInstance` / `MelonLogger`、`HarmonyInstance`。

### 組件屬性（`MelonLoader.*Attribute`）

- 必要：`MelonInfo(type, name, version, author)`、`MelonGame("sega-interactive", "Sinmai")`。`MelonGame(null, null)` 代表任何遊戲（MuMod 這樣寫）。
- 常用：
  - `MelonPriority(n)`：載入順序。
  - `MelonOptionalDependencies(...)`、`MelonAdditionalDependencies(...)`、`MelonIncompatibleAssemblies(...)`：相依與互斥。
  - `MelonGameVersion(...)`、`VerifyLoaderVersion(...)`、`VerifyLoaderBuild(...)`：限定版本。
  - `MelonColor`、`MelonAuthorColor`：日誌顏色。
  - `MelonID`、`MelonAdditionalCredits`、`MelonPlatform`、`MelonPlatformDomain`、`MelonProcess`。

### 啟動參數（反編譯 `MelonLaunchOptions`，加在 `Sinmai.exe` 後面，前綴 `--`）

- 主控台：`melonloader.hideconsole`、`melonloader.consoleontop`、`melonloader.consolemode`、`melonloader.consoledst`
- 日誌：`melonloader.debug`、`melonloader.hidewarnings`、`melonloader.maxlogs`、`melonloader.maxwarnings`、`melonloader.maxerrors`
- 載入：
  - `melonloader.loadmodemods` / `melonloader.loadmodeplugins`：值 0 / 1 / 2 = NORMAL / DEV / BOTH。
  - `melonloader.disablestartscreen`、`melonloader.disableunityclc`、`melonloader.unityversion`、`quitfix`
- 除錯：`melonloader.launchdebugger`
- `melonloader.agf*` 是 IL2CPP 用的，maimai 用不到。

### 動態載入 mod（MuMod 的做法）

MuMod（AquaMai 的更新器，Apache-2.0）本身是一個 `MelonGame(null, null)` 的小 mod：
1. 下載或讀快取 `LocalAssets\MuMod.cache` 的 AquaMai 位元組。
2. `Assembly.Load(bytes)`。
3. `MelonAssembly.LoadMelonAssembly(名稱, asm, true)`，再對每個 `LoadedMelons` 呼叫 `Register()`。

想做「自動更新的 mod」或「一個 DLL 帶多個 mod」可以照這個做。本機目前是直接放 `Mods\AquaMai.dll`（`MuMod.toml` 還在，但 `Mods` 裡沒有 `MuMod.dll`）。

## mod 專案設定

點歌台 mod 的 `.csproj`（節錄）：

```xml
<PropertyGroup>
  <TargetFramework>net48</TargetFramework>
  <LangVersion>9.0</LangVersion>
  <GameDir Condition="'$(GameDir)' == ''">H:\SDEZ1.70\Package</GameDir>
</PropertyGroup>
<ItemGroup>
  <PackageReference Include="Microsoft.NETFramework.ReferenceAssemblies" Version="1.0.3" PrivateAssets="all" />
</ItemGroup>
<ItemGroup>
  <!-- 全部 Private=false: 只拿來編譯, 不複製進輸出 -->
  <Reference Include="MelonLoader"><HintPath>$(GameDir)\MelonLoader\net35\MelonLoader.dll</HintPath><Private>false</Private></Reference>
  <Reference Include="0Harmony"><HintPath>$(GameDir)\MelonLoader\net35\0Harmony.dll</HintPath><Private>false</Private></Reference>
  <Reference Include="Assembly-CSharp"><HintPath>$(GameDir)\Sinmai_Data\Managed\Assembly-CSharp.dll</HintPath><Private>false</Private></Reference>
  <Reference Include="UnityEngine.CoreModule"><HintPath>$(GameDir)\Sinmai_Data\Managed\UnityEngine.CoreModule.dll</HintPath><Private>false</Private></Reference>
  <!-- 依需要加: UnityEngine.InputLegacyModule(鍵盤), ImageConversionModule(EncodeToPNG), AssetBundleModule… -->
</ItemGroup>
```

- 編譯：`dotnet build -c Release -p:GameDir="<遊戲 Package 目錄>"`，在 Linux 上也能編（只要有遊戲的 DLL 當參考）。
- 網頁、資料檔可以用 `EmbeddedResource` 內嵌進 DLL，安裝時只要丟一個檔案。
- **遊戲的 DLL 是專有檔案，不要放進公開 repo**，只在本機當編譯參考。

## mod 骨架

```csharp
[assembly: MelonInfo(typeof(MyMod.Mod), "MyMod", "1.0.0", "author")]
[assembly: MelonGame("sega-interactive", "Sinmai")]

public class Mod : MelonMod
{
    public override void OnInitializeMelon()     { /* 讀設定、掛 Harmony(屬性式補丁 MelonLoader 會自動套用) */ }
    public override void OnLateInitializeMelon() { /* 所有 mod 都初始化完之後: 適合起網頁伺服器等 */ }
    public override void OnUpdate()              { /* 每幀, 遊戲主執行緒: 碰遊戲物件 / Unity 一律在這裡 */ }
    public override void OnApplicationQuit()     { /* 收尾: 關外部程序、刪暫存設定 */ }
}
```

設定可以用 MelonLoader 內建的 `MelonPreferences`（存在 `UserData\MelonPreferences.cfg`），也可以自己讀寫一個檔案（點歌台用遊戲目錄下的 `SongRequestMod.toml`）。

## 除錯

- 看 `MelonLoader\Latest.log`；啟動時列出載入的 mod、補丁錯誤、例外。
- 遊戲閃退時 MelonLoader 會留下錯誤堆疊，先把 mod 移出 `Mods` 確認是不是 mod 造成的。
- 反編譯 `Assembly-CSharp.dll` 找方法名稱、欄位名稱、呼叫順序，是寫補丁前最重要的一步。
