# Voice Sentinel

一個語音健康監測應用，記錄音頻、分析語速和音高穩定度，並使用 Google Gemini 生成 AI 建議。

**快速導航：** [快速開始](#-快速開始) | [安裝](#-安裝) | [使用方式](#-使用方式) | [常見問題](#-常見問題)

---

## 快速開始

```powershell
# 1. 建立虛擬環境
python -m venv .venv

# 2. 啟動虛擬環境
.\.venv\Scripts\Activate.ps1

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 試試測試模式（無需麥克風、無需 API Key）
python voice_sentinel.py --test
---

## 安裝

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

## 使用方式

### 測試模式

```powershell
python voice_sentinel.py --test
```

- 無需麥克風、無需 API Key
- 使用合成語音測試
- 約 5-10 秒完成

### 完整模式（真實語音）

```powershell
python voice_sentinel.py
```

需要：麥克風 + 有效的 API Key + 網路

**流程：**
1. 錄製語音（說話 5 秒）
2. 分析語速和音高
3. AI 生成建議
4. 播放 AI 回應

### 自訂音檔分析

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

## 理解分析結果

### 核心指標

| 指標 | 含義 | 正常 |
|------|------|------|
| `rate` | 每秒語句段落數 | > 2.1 |
| `pitch_std` | 音高起伏程度 | > 10 |
| `abnormal` | 異常標記 | False |

### 結果示例

**正常：**
```json
{
  "rate": 3.5,
  "pitch_std": 45.3,
  "abnormal": false,
  "msg": "Normal"
}
```
建議：您的語音狀態很好！

**疲勞：**
```json
{
  "rate": 1.8,
  "pitch_std": 8.5,
  "abnormal": true,
  "msg": "Speech rate too slow - possible fatigue"
}
```
建議：建議休息或進食

### 異常判定

程式在以下情況標記為異常：
- 語速 < 基準值的 70%（可能疲勞）
- 音高標準差 < 10（能量感低）

---

## 進階設定

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

## 檔案說明

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

## 開始使用

```powershell
# 1. 先試測試模式
python voice_sentinel.py --test

# 2. 然後用真實語音試試
python voice_sentinel.py

# 3. 或用自訂音檔試試（推薦）
python analyze_audio.py your_audio.wav --ai
```
