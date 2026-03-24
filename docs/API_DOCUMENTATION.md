# Voice Sentinel - 後端 API 文檔

## 📋 系統概述

**項目名稱：** Voice Sentinel  
**描述：** 語音健康監測應用，分析話速和音高穩定度，使用 Google Gemini AI 生成建議  
**技術棧：** Python + FastAPI (可選) 或 CLI  
**當前狀態：** CLI 應用，需要前端介面整合

---

## 🏗️ 核心模組

### 1. **VoiceSentinel 類** (`voice_sentinel.py`)

主要功能類，負責音頻錄製、分析和 AI 生成。

#### 初始化參數
```python
VoiceSentinel(
    baseline_rate: float = 3.0,          # 基準語速（語句/秒）
    baseline_pitch: float = 120,         # 基準音高（Hz）
    test: bool = False                   # 測試模式（使用合成音頻）
)
```

#### 方法 1: 錄製音頻
```python
def record_audio() -> str
```
- **功能：** 錄製 5 秒的實時語音或合成測試音頻
- **返回值：** 音訊檔案路徑 (`input.wav`)
- **測試模式：** 自動生成合成音頻，無需麥克風

#### 方法 2: 分析語音健康
```python
def analyze_health(file_path: str) -> dict
```
- **功能：** 分析音頻的語速和音高特徵
- **輸入：** 音訊檔案路徑 (`.wav`, `.mp3`, `.flac`, `.ogg`)
- **輸出：**
```json
{
  "rate": 3.5,                          # 語速（語句/秒）0-10
  "pitch_std": 45.3,                    # 音高標準差（越高越波動）0-200
  "abnormal": false,                    # 是否異常狀態
  "msg": "Normal state detected"        # 診斷訊息
}
```

#### 方法 3: 獲取 AI 回應
```python
async def get_ai_response(analysis: dict) -> str
```
- **功能：** 使用 Google Gemini 根據分析結果生成建議
- **輸入：** `analyze_health()` 的返回結果
- **輸出：** AI 生成的建議文本（50 字以內）
- **示例：**
```
"You sound a bit tired. Please take a break and drink some water."
```

#### 方法 4: 文字轉語音播放
```python
async def speak(text: str) -> None
```
- **功能：** 使用 Edge TTS 播放 AI 回應
- **輸入：** 要播放的文本
- **輸出：** 生成 `output.mp3` 並自動播放（Windows）

---

## 📊 數據結構

### 分析結果對象
```typescript
interface AnalysisResult {
  rate: number;              // 語速 (語句/秒)
  pitch_std: number;         // 音高標準差
  abnormal: boolean;         // 是否異常
  msg: string;              // 診斷訊息
}
```

### 異常判定規則
| 條件 | 判定 | 建議 |
|------|------|------|
| `rate < baseline_rate × 0.6` | 語速過慢 | 休息/進食 |
| `pitch_std < 10` | 音高平板 | 進食/飲水 |
| 兩者都正常 | ✅ 正常 | 保持良好狀態 |

### 基準值建議
- **語速基準：** 3.0-3.5 語句/秒（中文自然語速）
- **音高基準：** 120-140 Hz（因人而異）

---

## 🚀 使用流程

### 流程圖
```
1. 用戶啟動 → 選擇模式
   ├─ 測試模式：無需麥克風，使用合成音頻
   └─ 實時模式：需要麥克風

2. 錄製/上傳音頻
   └─ record_audio() 或 上傳音檔

3. 分析語音特徵
   └─ analyze_health(file_path) → AnalysisResult

4. 生成 AI 建議
   └─ await get_ai_response(analysis) → str

5. 播放 AI 回應
   └─ await speak(response_text)
```

---

## 🎯 前端集成指南

### 建議的 API 端點（如果轉為 REST API）

#### 1. 分析音頻
```
POST /api/analyze
Content-Type: multipart/form-data

Body:
  - file: [Audio File]
  - baseline_rate: 3.0 (optional)
  - baseline_pitch: 120 (optional)

Response:
{
  "rate": 3.5,
  "pitch_std": 45.3,
  "abnormal": false,
  "msg": "Normal state detected",
  "ai_response": "You sound great! Keep it up."
}
```

#### 2. 獲取診斷建議
```
POST /api/diagnose
Content-Type: application/json

Body:
{
  "rate": 3.5,
  "pitch_std": 45.3,
  "abnormal": false,
  "msg": "Normal state detected"
}

Response:
{
  "ai_suggestion": "You sound great! Keep it up.",
  "audio_url": "/files/output.mp3"
}
```

#### 3. 錄音並分析
```
POST /api/record-and-analyze
Content-Type: application/json

Body:
{
  "duration": 5,
  "test_mode": false
}

Response:
{
  "rate": 3.5,
  "pitch_std": 45.3,
  "abnormal": false,
  "msg": "Normal state detected",
  "ai_response": "You sound great!",
  "audio_url": "/files/input.wav"
}
```

---

## 🔧 配置參數

### 環境變數 (`.env`)
```env
GOOGLE_API_KEY=your_api_key_here
```

### 常量（可配置）
```python
FS = 16000              # 採樣率
DURATION = 5            # 預設錄音時長（秒）
FILENAME = "input.wav"  # 輸入音訊檔案名
```

---

## 📁 文件結構

```
├── voice_sentinel.py        # 核心 VoiceSentinel 類
├── analyze_audio.py         # CLI 音檔分析工具
├── quickstart.py           # 互動式選單
├── result_interpreter.py   # 結果演示工具
├── requirements.txt        # 依賴列表
├── .env                   # API Key 設定
└── API_DOCUMENTATION.md   # 本文件
```

---

## 📦 依賴清單

```
numpy
librosa           # 音頻分析
sounddevice       # 麥克風錄音
soundfile         # 音檔讀寫
edge-tts          # 文字轉語音
google-generativeai  # Gemini API
python-dotenv     # 環境變數
```

---

## ⚠️ 錯誤處理

### 常見異常
| 錯誤 | 原因 | 解決方案 |
|------|------|--------|
| `No module named 'dotenv'` | 缺少依賴 | `pip install python-dotenv` |
| `ModuleNotFoundError: No module named 'google'` | 缺少 Gemini SDK | `pip install google-generativeai` |
| `GOOGLE_API_KEY not found` | 未設定 API Key | 編輯 `.env` 檔案 |
| `sounddevice failed` | 麥克風未連接 | 使用測試模式或上傳音檔 |

### Fallback 機制
- 如果 Gemini API 失敗，使用預設回應
- 如果 TTS 失敗，直接顯示文本
- 測試模式永遠有效（無需網路和 API）

---

## 🎨 UI 建議

### 推薦的前端功能

#### 首頁
- [ ] 選擇模式按鈕（測試 / 實時 / 上傳檔案）
- [ ] 基準值設定（語速、音高）

#### 錄音介面
- [ ] 開始/停止錄音按鈕
- [ ] 倒計時顯示
- [ ] 實時波形圖

#### 結果展示
- [ ] 分析結果表格（語速、音高、狀態）
- [ ] 狀態指示（✅ 正常 / ⚠️ 異常）
- [ ] AI 建議展示
- [ ] 播放 AI 回應音頻

#### 歷史記錄
- [ ] 保存分析結果列表
- [ ] 對比不同時間的數據

---

## 🧪 測試建議

### 測試用例
```python
# 測試模式示例
sentinel = VoiceSentinel(test=True)
audio = sentinel.record_audio()  # 生成合成音頻
result = sentinel.analyze_health(audio)
print(result)
```

### 預期輸出
```json
{
  "rate": 2.5,
  "pitch_std": 35.0,
  "abnormal": false,
  "msg": "Normal state detected"
}
```

---

## 📞 集成支持

### 快速開始清單
- [ ] 安裝 Python 依賴：`pip install -r requirements.txt`
- [ ] 設定 Google API Key 到 `.env` 檔案
- [ ] 測試後端：`python voice_sentinel.py --test`
- [ ] 根據本文檔設計前端 UI
- [ ] 將前端與後端整合（REST API 或直接調用）

### 推薦的前端框架
- **Web：** React / Vue.js / Next.js
- **Desktop：** Electron / Tauri
- **Mobile：** React Native / Flutter

---

## 📝 版本日誌

- **v1.0** (2026-03-22)
  - 核心分析功能完成
  - Gemini AI 整合
  - TTS 播放功能
  - 文件可視化基準

---

此文檔可直接提交給前端開發者或 Claude AI。祝你集成順利！ 🚀
