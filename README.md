# 🎤 Voice Sentinel

一個語音健康監測應用，記錄音頻、分析語速和音高穩定度，並使用 Google Gemini 生成 AI 建議。

**快速導航：** [快速開始](#-快速開始) | [安裝](#-安裝) | [使用方式](#-使用方式) | [常見問題](#-常見問題)

---

## ⚡ 快速開始（3 分鐘）

```powershell
# 1. 建立虛擬環境
python -m venv .venv

# 2. 啟動虛擬環境
.\.venv\Scripts\Activate.ps1

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 試試測試模式（無需麥克風、無需 API Key）
python voice_sentinel.py --test
```

✅ 無需麥克風 | ✅ 無需 API Key | ✅ 完全離線

---

## 🚀 安裝

### 步驟 1：建立虛擬環境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 步驟 2：安裝依賴

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

如果 `sounddevice` 安裝失敗（Windows）：
```powershell
pip install pipwin
pipwin install sounddevice
```

### 步驟 3：設定 API Key（可選）

編輯或複製 `.env` 檔案：

```
GOOGLE_API_KEY=your_actual_api_key_here
```

驗證設置：
```powershell
python voice_sentinel.py --test
```

---

## 📖 使用方式

### 1️⃣ 測試模式（推薦先試）

```powershell
python voice_sentinel.py --test
```

- 無需麥克風、無需 API Key
- 使用合成語音測試
- 約 5-10 秒完成

### 2️⃣ 完整模式（真實語音）

```powershell
python voice_sentinel.py
```

需要：麥克風 + 有效的 API Key + 網路

**流程：**
1. 🎤 錄製語音（說話 5 秒）
2. 🔍 分析語速和音高
3. 🤖 AI 生成建議
4. 🔊 播放 AI 回應

### 3️⃣ 自訂音檔分析✨（推薦）

**最好用的方式** - 分析你自己的錄音：

```powershell
# 基本分析
python analyze_audio.py your_voice.wav

# 包含 AI 回應
python analyze_audio.py your_voice.wav --ai

# 自訂基準值
python analyze_audio.py your_voice.wav --rate 3.5 --pitch 140
```

支持格式：`.wav` | `.mp3` | `.flac` | `.ogg`

優點：
- 無需麥克風
- 可分析過去的錄音
- 可對比不同時間的語音
- 適合離線分析

---

## 📊 理解分析結果

### 核心指標

| 指標 | 含義 | 正常 |
|------|------|------|
| `rate` | 每秒語句段落數 | > 2.1 |
| `pitch_std` | 音高起伏程度 | > 10 |
| `abnormal` | 異常標記 | False |

### 結果示例

**✅ 正常：**
```json
{
  "rate": 3.5,
  "pitch_std": 45.3,
  "abnormal": false,
  "msg": "Normal"
}
```
💡 建議：您的語音狀態很好！

**⚠️ 疲勞：**
```json
{
  "rate": 1.8,
  "pitch_std": 8.5,
  "abnormal": true,
  "msg": "Speech rate too slow - possible fatigue"
}
```
💡 建議：建議休息或進食

### 異常判定

程式在以下情況標記為異常：
- 語速 < 基準值的 70%（可能疲勞）
- 音高標準差 < 10（能量感低）

---

## ⚙️ 進階設定

### 修改錄音時間

編輯 `voice_sentinel.py` 第 58 行：

```python
DURATION = 10  # 改成 10 秒（默認 5 秒）
```

### 個人化基準值

在 `voice_sentinel.py` 的 `main()` 函數中：

```python
sentinel = VoiceSentinel(
    baseline_pitch=140,   # 你的基準音高
    baseline_rate=3.5,    # 你的基準語速
    test=False
)
```

**建立個人基準的方法：**
1. 在精力充沛時進行 3-5 次測試
2. 記錄每次的 `rate` 和 `pitch_std`
3. 計算平均值
4. 使用平均值作為基準

---

## 📁 檔案說明

| 檔案 | 說明 |
|------|------|
| `voice_sentinel.py` | 核心程式 |
| `analyze_audio.py` | 自訂音檔分析工具 |
| `quickstart.py` | 互動式選單 |
| `result_interpreter.py` | 結果演示工具 |
| `requirements.txt` | Python 依賴 |
| `.env` | API Key 設定 |
| `.env.example` | 設定範本 |

---

## 🆘 常見問題

### ❓ 錄不到麥克風

**檢查麥克風列表：**
```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```

**檢查 Windows 隱私權限：**
1. 設定 → 隱私權與安全性 → 麥克風
2. 允許應用存取麥克風
3. 重新啟動應用

### ❓ API Key 不生效

確認：
1. ✅ `.env` 檔案在專案根目錄
2. ✅ 格式正確：`GOOGLE_API_KEY=your_key_here`（無空格、無引號）
3. ✅ API Key 有效且已啟用

驗證：
```powershell
python voice_sentinel.py --test
```

若看到 `[INFO] Environment variables loaded from .env` ✅ 成功

### ❓ 播放音訊失敗

**Windows：** 自動播放 `output.mp3`（檢查檔案是否建立）

**Mac/Linux：** 安裝播放工具
```bash
pip install playsound
```

或手動打開 `output.mp3` 檔案

### ❓ 無法加載音檔

**原因：** 檔案格式不支持或損壞

**解決：** 安裝 ffmpeg

```powershell
# Windows (Chocolatey)
choco install ffmpeg

# Mac (Homebrew)
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg
```

### ❓ Google API 或計費問題

確認：
1. Google Cloud 帳戶已啟用 Generative AI API
2. Billing 已正確設置
3. API Key 具有正確的權限

---

## 💡 最佳實踐

### 1️⃣ 建立個人基準

在精力充沛時進行 3-5 次測試，使用平均值作為基準

### 2️⃣ 定期監測

每天同一時間進行測試，追蹤長期變化

### 3️⃣ 環境一致性

在同一位置、同一麥克風進行測試，確保準確性

### 4️⃣ 記錄上下文

記錄睡眠、飲食、壓力等因素，幫助分析

---

## 📚 快速命令參考

```powershell
# 啟動虛擬環境
.\.venv\Scripts\Activate.ps1

# 測試模式（推薦先執行）
python voice_sentinel.py --test

# 完整模式（需要麥克風和 API Key）
python voice_sentinel.py

# 互動式選單
python quickstart.py

# 自訂音檔分析（推薦）✨
python analyze_audio.py your_voice.wav --ai

# 查看分析結果演示
python result_interpreter.py

# 查看幫助
python voice_sentinel.py --help
python analyze_audio.py --help

# 檢查麥克風
python -c "import sounddevice as sd; print(sd.query_devices())"
```

---

## ✅ 推薦使用流程

### 首次使用

1. 試試測試模式驗證環境
2. 如果成功，試試完整模式
3. 建立你的個人基準（3-5 次測試）

### 日常使用

使用自訂音檔分析（推薦）：
```powershell
python analyze_audio.py your_voice.wav --ai
```

---

## 🎉 開始使用

```powershell
# 1. 先試測試模式
python voice_sentinel.py --test

# 2. 然後用真實語音試試
python voice_sentinel.py

# 3. 或用自訂音檔試試（推薦）
python analyze_audio.py your_audio.wav --ai
```

**祝您使用愉快！** 🎤

---

**API Key 狀態：** ✅ 有效  
**最後更新：** 2026-03-20  
**版本：** 1.0
