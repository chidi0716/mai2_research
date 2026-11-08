# CLAUDE.md

maimai DX（Sinmai.exe）MelonLoader mod 的研究知識庫。使用者 chidi0716 會用它來寫各種 mod，包括點歌台、其他功能 mod、改貼圖和音效等。

## 開始工作前

- 先讀 [`AI_CONTEXT.md`](AI_CONTEXT.md)：全部內容的濃縮版。需要細節或範例時，再讀 `docs/` 裡對應的章節（目錄在 `README.md`）。
- 遊戲成員名稱來自反編譯，不同版本可能不同。寫補丁前，先用使用者提供的 `Assembly-CSharp.dll` 確認。

## 溝通

- 用繁體中文回覆，簡潔，不要長篇大論。

## 規則

- **不放任何遊戲檔案**：DLL、音效、圖片、影片、資料包都不進 repo（包括解出來的音效和反編譯出來的完整原始碼）。使用者上傳的遊戲檔案只在本機暫存區分析。
- **commit 作者**是 `chidi0716 <128954796+chidi0716@users.noreply.github.com>`。**不要**加 `Co-Authored-By`、`Claude-Session` 等署名，也不要在任何地方寫 Claude 是貢獻者。
- 直接在 `main` 上工作並推送；沒被要求就不要開 PR。
- 授權：GPLv3（MaiL2d、maimai-dghub-link）或沒有標明授權（扫码点歌；NGO 銘牌包、maimai-ngo 無授權檔但發布者公開歡迎 fork）的專題，只記做法和遊戲入口，不複製程式碼。
- 第三方工具（例如 vgmstream 的 clHCA）不放進 repo，只寫下載方式。

## 更新知識庫

- 有新發現時，同時更新對應的 `docs/` 章節**和** `AI_CONTEXT.md`；新增章節時也要更新 `README.md` 的目錄。
- 每一條都要有根據（原始碼、反編譯、實測）。沒驗證過的內容要明確標成「未驗證」，或乾脆不寫。
- 踩到的坑記到 `docs/05-踩坑紀錄.md`，表格依編號排序。
- 尚未研究的部分（影片的載入方式、UI 預製物結構、連線伺服器）研究完再補。選項包結構、貼圖載入、按鍵來源已寫在 docs/10、11。
