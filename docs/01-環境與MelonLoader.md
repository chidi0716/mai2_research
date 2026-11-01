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
| SDEZ | 日版 | 1.60、1.65、1.66、1.70 |
| SDGB | 國服（中國版），版本字串像 `Ver.CN1.56-B` | 1.50、1.55 |

- 主要成員（Process、`GameManager`、`GamePlayManager`、`NotesManager`、判定入口 `JudgeResultSt.UpdateScore`）在 SDGB 1.50～SDEZ 1.66 都還在，但細節欄位會變。
- 部分 SDEZ 1.66 包體用外置的 AMDaemon 執行環境：`Sinmai_Data\Plugins\amdaemon_api.dll` 和 `Sinmai_Data\Managed\AMDaemon.NET.dll` 必須是同一套；要先啟動 AMDaemon 再啟動 Sinmai（用包體附的啟動批次檔），直接點 `Sinmai.exe` 會因為沒有 IPC 對端而起不來。

> 不同遊戲版本（例如 1.65 / 1.70）的 `Assembly-CSharp.dll` 內容不同。寫 mod 時要確認用的是哪一版；有些 mod 會直接以 DLL 的 SHA-256 標明只驗證過哪個版本。

## MelonLoader

- 版本：0.6.4（Mono 版）。內含 HarmonyX（`MelonLoader\net35\0Harmony.dll`）。
- 目錄：
  - `Package\LocalAssets\…`：多個 mod 慣用的本機資源資料夾（例如 MaiL2d 模型、DxPassCompat 自製卡圖）
  - `Package\Sinmai_Data\Plugins\`：原生 DLL（MaiL2d 會在這裡放 `Live2DCubismCore.dll`）
  - `Package\Mods\*.dll`：mod 本體
  - `Package\UserData\MelonPreferences.cfg`：`MelonPreferences` 存的設定
  - `Package\MelonLoader\Latest.log`：日誌（mod 的 `LoggerInstance.Msg` / `MelonLogger.Msg` 都在這裡，會自動加上 `[mod 名稱]` 前綴）

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
