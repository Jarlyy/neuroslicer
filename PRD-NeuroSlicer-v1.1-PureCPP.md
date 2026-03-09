# Product Requirements Document (PRD)
## NeuroSlicer - AI-ассистированный слайсер для 3D-печати

**Версия:** 1.1 (Обновлено: Pure C++)  
**Дата:** 2 марта 2026  
**Автор:** NeuroSlicer Team  
**Статус:** Черновик

---

## 1. Обзор приложения и цели

### 1.1 Описание
NeuroSlicer - это интеллектуальное расширение для OrcaSlicer, которое использует большие языковые модели (LLM) для автоматической диагностики дефектов 3D-печати и оптимизации параметров слайсинга. Система анализирует текстовые описания проблем пользователя и предлагает конкретные изменения в профилях печати для улучшения качества.

### 1.2 Цели проекта
- **Снизить порог входа** в 3D-печать для новичков
- **Автоматизировать** процесс настройки профилей печати
- **Уменьшить количество брака** за счет интеллектуальных рекомендаций
- **Сохранить время** опытных пользователей на диагностику проблем
- **Создать базу знаний** о дефектах и их решениях в формате, понятном AI

### 1.3 Ключевая ценность
Пользователь описывает проблему естественным языком → AI анализирует → предлагает конкретные параметры → применяет изменения к профилю.

---

## 2. Целевая аудитория

### 2.1 Первичная аудитория
- **Новички в 3D-печати** (0-6 месяцев опыта)
  - Не знают, как настраивать параметры
  - Путаются в терминологии слайсеров
  - Часто получают дефекты, не понимая причин
  - Нуждаются в простых объяснениях на русском языке

### 2.2 Вторичная аудитория  
- **Опытные пользователи** (6+ месяцев)
  - Хотят быстро решать нестандартные проблемы
  - Ищут оптимальные настройки для новых материалов
  - Ценят экономию времени на эксперименты

### 2.3 Третичная аудитория
- **Малое производство и мейкеры**
  - Печатают серии деталей
  - Нуждаются в стабильности процесса
  - Готовы использовать AI для оптимизации

---

## 3. Основные функции и функциональность

### 3.1 Функция: AI-диагностика дефектов (текстовый ввод)

**Описание:** Пользователь вводит текстовое описание проблемы с печатью, AI анализирует и предлагает решения.

**Технические детали:**
- **Вход:** Текстовое описание дефекта (на русском или английском)
- **AI-модель:** gpt-oss через Hugging Face Inference API
- **База знаний:** Структурированный JSON-датасет из 29 категорий дефектов (2666 строк)
- **Выход:** Список изменений (diff) для профиля OrcaSlicer
- **Реализация:** C++ с libcurl (HTTP) и nlohmann/json (JSON)

**Критерии приемки:**
- [ ] Пользователь может ввести описание дефекта на естественном языке
- [ ] AI корректно идентифицирует тип дефекта из 29 категорий
- [ ] AI предлагает 1-3 возможных причины с объяснениями
- [ ] AI возвращает конкретные изменения параметров с рекомендуемыми значениями
- [ ] AI объясняет, почему предложены именно эти изменения
- [ ] Время отклика API < 10 секунд
- [ ] Поддержка русского и английского языков

**Пример взаимодействия:**
```
Пользователь: "Слои расслаиваются, деталь ломается по слоям"

AI отвечает:
- Проблема: Layer Separation / Расслоение слоев
- Причины: 
  1. Низкая температура печати
  2. Слишком высокая скорость охлаждения
- Рекомендации:
  • nozzle_temperature: +10°C (с 200 до 210)
  • fan_speed_first_layer: 0% (отключить обдув первых слоев)
  • print_speed: -20% (уменьшить скорость)
```

**Пример кода (C++):**
```cpp
// NeuroAIClient.h
#pragma once
#include <string>
#include <vector>
#include <nlohmann/json.hpp>

struct AIRecommendation {
    std::string parameter;
    double current_value;
    double suggested_value;
    std::string reason;
    std::string category;
};

struct AIResponse {
    std::string defect_type;
    double confidence;
    std::vector<std::string> causes;
    std::vector<AIRecommendation> recommendations;
};

class NeuroAIClient {
public:
    NeuroAIClient(const std::string& api_token);
    AIResponse analyzeDefect(const std::string& user_input);
    
private:
    std::string api_token_;
    std::string buildPrompt(const std::string& user_input);
    std::string makeHttpRequest(const std::string& json_payload);
    AIResponse parseResponse(const std::string& response);
};
```

### 3.2 Функция: Интеллектуальная корректировка профилей

**Описание:** AI анализирует текущий профиль и предлагает оптимизации на основе описанных проблем.

**Технические детали:**
- **Формат входных данных:** Файл профиля OrcaSlicer (.ini, .json)
- **Формат выходных данных:** Diff-список изменений (параметр: старое_значение → новое_значение)
- **Параметры для изменения:** Все параметры профиля OrcaSlicer
- **Реализация:** C++ парсер профилей + применитель изменений

**Критерии приемки:**
- [ ] Система парсит профили OrcaSlicer всех форматов (.ini, .json)
- [ ] AI может менять любые параметры профиля
- [ ] AI возвращает только измененные параметры (diff)
- [ ] Каждое изменение сопровождается объяснением
- [ ] Показ предпросмотра изменений перед применением
- [ ] Подтверждение пользователя обязательно перед применением

**Пример кода (C++):**
```cpp
// ProfileManager.h
#pragma once
#include <string>
#include <map>
#include <vector>

struct ProfileParameter {
    std::string name;
    std::string value;
    std::string section;  // для .ini файлов
};

struct ProfileDiff {
    std::string parameter;
    std::string old_value;
    std::string new_value;
    std::string reason;
};

class ProfileManager {
public:
    // Загрузка профиля
    bool loadProfile(const std::string& filepath);
    
    // Применение изменений от AI
    std::vector<ProfileDiff> applyAIRecommendations(
        const std::vector<AIRecommendation>& recommendations
    );
    
    // Сохранение профиля
    bool saveProfile(const std::string& filepath);
    
    // Получение текущего значения параметра
    std::string getParameter(const std::string& name);
    
    // Установка значения параметра
    void setParameter(const std::string& name, const std::string& value);
    
private:
    std::map<std::string, ProfileParameter> parameters_;
    std::string profile_format_;  // "ini" или "json"
    
    bool parseIniFile(const std::string& filepath);
    bool parseJsonFile(const std::string& filepath);
    bool saveIniFile(const std::string& filepath);
    bool saveJsonFile(const std::string& filepath);
};
```

### 3.3 Функция: Интерактивный чат с AI-ассистентом

**Описание:** Интегрированная панель чата в интерфейсе OrcaSlicer для диалога с AI.

**Технические детали:**
- **Интеграция:** wxWidgets панель в окне OrcaSlicer
- **История:** Сохранение контекста диалога (последние 5 сообщений)
- **Язык:** Переключение русский/английский
- **API:** Hugging Face Inference API через libcurl
- **Потоковость:** Асинхронные запросы (wxThread) для неблокирующего UI

**Критерии приемки:**
- [ ] Панель чата встраивается в интерфейс OrcaSlicer
- [ ] Пользователь может задавать уточняющие вопросы
- [ ] AI помнит контекст предыдущих сообщений
- [ ] Поддержка переключения языка интерфейса (RU/EN)
- [ ] Возможность копировать ответы AI
- [ ] История диалога сохраняется в рамках сессии
- [ ] UI не блокируется во время запроса к API

**Пример кода (C++):**
```cpp
// NeuroChatPanel.h
#pragma once
#include <wx/wx.h>
#include <wx/thread.h>
#include <vector>
#include <memory>
#include "NeuroAIClient.h"

struct ChatMessage {
    bool is_user;
    wxString text;
    wxDateTime timestamp;
};

class AIRequestThread : public wxThread {
public:
    AIRequestThread(NeuroAIClient* client, const wxString& message);
    virtual ExitCode Entry() override;
    
private:
    NeuroAIClient* client_;
    wxString message_;
};

class NeuroChatPanel : public wxPanel {
public:
    NeuroChatPanel(wxWindow* parent);
    ~NeuroChatPanel();
    
    // Отправка сообщения
    void SendMessage(const wxString& message);
    
    // Переключение языка
    void SetLanguage(const wxString& lang);  // "ru" или "en"
    
private:
    // UI элементы
    wxTextCtrl* chat_history_;
    wxTextCtrl* input_field_;
    wxButton* send_button_;
    wxChoice* language_selector_;
    wxGauge* progress_indicator_;
    
    // Данные
    std::vector<ChatMessage> messages_;
    std::unique_ptr<NeuroAIClient> ai_client_;
    AIRequestThread* current_request_;
    wxString current_language_;
    
    // Обработчики событий
    void OnSendButton(wxCommandEvent& event);
    void OnInputEnter(wxCommandEvent& event);
    void OnLanguageChange(wxCommandEvent& event);
    void OnAIResponse(wxThreadEvent& event);
    void OnAIError(wxThreadEvent& event);
    
    // Вспомогательные методы
    void AddMessageToHistory(const ChatMessage& msg);
    void ShowTypingIndicator(bool show);
    wxString BuildSystemPrompt();
    
    wxDECLARE_EVENT_TABLE();
};
```

### 3.4 Функция: Подготовка к анализу фото (заглушка)

**Описание:** Архитектура готова для будущей интеграции LLaVA для анализа фото дефектов.

**Технические детали:**
- **Интерфейс:** Кнопка "Загрузить фото" (визуально присутствует, но неактивна)
- **Будущая интеграция:** LLaVA через Hugging Face API
- **Сообщение:** "Функция анализа фото появится в следующей версии"

**Критерии приемки:**
- [ ] UI-элементы для загрузки фото присутствуют
- [ ] При попытке использования показывается информативное сообщение
- [ ] Архитектура поддерживает добавление функционала без рефакторинга

---

## 4. Рекомендации по техническому стеку

### 4.1 Backend/AI Core (C++)

**Язык:** C++17 (или C++20 если поддерживается компилятором)

**Библиотеки:**
- **HTTP клиент:** libcurl (стандарт де-факто для C++)
  ```cpp
  // Пример использования libcurl
  CURL* curl = curl_easy_init();
  curl_easy_setopt(curl, CURLOPT_URL, "https://api-inference.huggingface.co/models/...");
  curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_payload.c_str());
  curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
  curl_easy_perform(curl);
  ```

- **JSON парсер:** nlohmann/json (header-only, удобный синтаксис)
  ```cpp
  // Пример использования nlohmann/json
  #include <nlohmann/json.hpp>
  using json = nlohmann::json;
  
  json j = json::parse(response_string);
  std::string defect_type = j["analysis"]["defect_type"];
  ```

- **INI парсер:** inih или собственная реализация
- **Ведение логов:** spdlog (современная C++ библиотека для логов)

**AI-модель:**
- **API:** Hugging Face Inference API
- **Модель:** gpt-oss (текстовая генерация)
- **Альтернативы:**
  - **OpenAI API (GPT-4):** ❌ Платный, требует VPN в РФ
  - **Hugging Face Inference:** ✅ Бесплатный (30k запросов/мес), доступен в РФ
  - **Ollama (локально):** ❌ Требует GPU 6GB+
  - **DeepSeek API:** ⚠️ Доступен, но менее стабилен

**Выбор:** Hugging Face Inference API с gpt-oss

### 4.2 Интеграция с OrcaSlicer

- **Тип:** Форк исходного кода OrcaSlicer
- **UI Framework:** wxWidgets 3.2+ (как в оригинальном OrcaSlicer)
- **Язык:** C++17
- **Архитектура:** Монолитное приложение (один процесс)

**Интеграционные точки:**
1. **Новая панель:** Добавление `NeuroChatPanel` в главное окно
2. **Меню:** Пункт "Tools" → "AI Assistant" (Ctrl+Shift+A)
3. **Toolbar:** Кнопка быстрого доступа к AI-ассистенту
4. **Контекстное меню:** Правый клик на профиле → "Analyze with AI"

### 4.3 Форматы данных

- **Профили OrcaSlicer:** .ini, .json
- **База знаний:** JSON (структурированный датасет)
- **Конфигурация:** config.json (API ключи, настройки)
- **Логи:** .log файлы (spdlog)
- **Кэш:** SQLite (для кэширования ответов AI)

### 4.4 Инструменты разработки

- **Сборка:** CMake 3.16+
- **Компилятор:** 
  - Windows: MSVC 2019+
  - Linux: GCC 9+
  - macOS: Clang 12+
- **Версионирование:** Git
- **Тестирование:** Google Test
- **Документация:** Doxygen

### 4.5 Структура проекта

```
neuro-slicer/
├── CMakeLists.txt
├── src/
│   ├── ai/                          # AI модуль
│   │   ├── NeuroAIClient.cpp/.h     # HTTP клиент для HF API
│   │   ├── PromptBuilder.cpp/.h     # Генератор промптов
│   │   └── ResponseParser.cpp/.h    # Парсер ответов AI
│   ├── core/                        # Ядро системы
│   │   ├── ProfileManager.cpp/.h    # Работа с профилями
│   │   ├── ConfigManager.cpp/.h     # Управление настройками
│   │   └── KnowledgeBase.cpp/.h     # База знаний (JSON)
│   ├── ui/                          # Интерфейс wxWidgets
│   │   ├── NeuroChatPanel.cpp/.h    # Панель чата
│   │   ├── RecommendationDialog.cpp/.h  # Диалог рекомендаций
│   │   └── NeuroPlugin.cpp/.h       # Точка входа плагина
│   └── utils/                       # Утилиты
│       ├── HttpClient.cpp/.h        # Обертка над libcurl
│       ├── Logger.cpp/.h            # Логирование
│       └── StringUtils.cpp/.h       # Работа со строками
├── data/
│   ├── knowledge_base.json          # База знаний о дефектах
│   └── prompts/                     # Шаблоны промптов
│       ├── system_prompt_en.txt
│       └── system_prompt_ru.txt
├── resources/                       # Иконки, переводы
├── tests/                           # Unit тесты
└── docs/                            # Документация
```

---

## 5. Концептуальная модель данных

### 5.1 Структура базы знаний (JSON)

```json
{
  "version": "1.0",
  "last_updated": "2026-03-02",
  "defects": [
    {
      "id": "layer_separation",
      "name": {
        "en": "Layer Separation",
        "ru": "Расслоение слоев"
      },
      "symptoms": {
        "en": ["Layers splitting apart", "Weak layer adhesion", "Part breaks along layer lines"],
        "ru": ["Слои разделяются", "Слабая адгезия слоев", "Деталь ломается по линиям слоев"]
      },
      "causes": [
        {
          "en": "Low printing temperature",
          "ru": "Низкая температура печати",
          "priority": 1
        },
        {
          "en": "Excessive cooling",
          "ru": "Чрезмерное охлаждение",
          "priority": 2
        }
      ],
      "solutions": [
        {
          "parameter": "nozzle_temperature",
          "adjustment": "+10",
          "unit": "celsius",
          "min_value": 180,
          "max_value": 280,
          "reason": {
            "en": "Higher temperature improves inter-layer adhesion",
            "ru": "Повышение температуры улучшает межслойную адгезию"
          }
        },
        {
          "parameter": "fan_speed_first_layer",
          "adjustment": "=0",
          "unit": "percent",
          "min_value": 0,
          "max_value": 100,
          "reason": {
            "en": "Disable cooling for first layers to prevent rapid cooling",
            "ru": "Отключите обдув первых слоев для предотвращения быстрого охлаждения"
          }
        }
      ],
      "materials_affected": ["PLA", "ABS", "PETG"],
      "severity": "high"
    }
  ]
}
```

### 5.2 C++ структуры данных

```cpp
// KnowledgeBase.h
#pragma once
#include <string>
#include <vector>
#include <map>
#include <nlohmann/json.hpp>

struct LocalizedString {
    std::string en;
    std::string ru;
    
    std::string get(const std::string& lang) const {
        return lang == "ru" ? ru : en;
    }
};

struct DefectCause {
    LocalizedString description;
    int priority;  // 1 = highest
};

struct ParameterChange {
    std::string parameter;
    std::string adjustment;  // "+10", "-5", "=0"
    std::string unit;
    double min_value;
    double max_value;
    LocalizedString reason;
};

struct DefectInfo {
    std::string id;
    LocalizedString name;
    std::map<std::string, std::vector<std::string>> symptoms;  // lang -> symptoms
    std::vector<DefectCause> causes;
    std::vector<ParameterChange> solutions;
    std::vector<std::string> materials_affected;
    std::string severity;  // "low", "medium", "high"
};

class KnowledgeBase {
public:
    bool loadFromFile(const std::string& filepath);
    std::vector<DefectInfo> findDefectsBySymptom(
        const std::string& symptom, 
        const std::string& lang
    );
    DefectInfo getDefect(const std::string& defect_id);
    
private:
    std::map<std::string, DefectInfo> defects_;
    std::string version_;
};
```

### 5.3 Структура AI-ответа

```cpp
// AIResponse.h
#pragma once
#include <string>
#include <vector>

struct ParameterRecommendation {
    std::string category;        // "temperature", "speed", "cooling"
    std::string parameter;       // "nozzle_temperature"
    double current_value;
    double suggested_value;
    std::string change_type;     // "increment", "set"
    double change_value;
    std::string explanation;     // Почему это изменение
    int priority;               // 1 = highest
};

struct AIResponse {
    struct Analysis {
        std::string defect_type;           // "layer_separation"
        std::string defect_name_localized; // "Расслоение слоев"
        double confidence;                 // 0.0 - 1.0
        std::vector<std::string> causes;
    } analysis;
    
    std::vector<ParameterRecommendation> recommendations;
    std::vector<std::string> additional_tips;
    std::string warning;  // Опциональное предупреждение
};
```

### 5.4 Структура конфигурации

```cpp
// Config.h
#pragma once
#include <string>

struct NeuroConfig {
    // API настройки
    std::string hf_api_token;
    std::string hf_model_name = "gpt-oss";
    std::string hf_api_url = "https://api-inference.huggingface.co/models/";
    
    // UI настройки
    std::string default_language = "ru";
    bool show_confidence_scores = true;
    int max_recommendations = 5;
    
    // Производительность
    int api_timeout_seconds = 30;
    bool enable_response_cache = true;
    int cache_ttl_minutes = 60;
    
    // Отладка
    bool enable_logging = true;
    std::string log_level = "info";  // "debug", "info", "warning", "error"
    
    bool loadFromFile(const std::string& filepath);
    bool saveToFile(const std::string& filepath);
};
```

---

## 6. Принципы дизайна пользовательского интерфейса

### 6.1 Интеграция в OrcaSlicer

**Расположение панели:**
- Правая боковая панель (под "Process" или отдельная вкладка)
- Ширина: 350-400px
- Высота: адаптивная (минимум 500px)

**Вкладки панели:**
1. **"Чат" / "Chat"** - Основной интерфейс диалога (активная по умолчанию)
2. **"История" / "History"** - Предыдущие диагностики текущей сессии
3. **"Настройки" / "Settings"** - API ключ, язык, логирование

### 6.2 Компоненты панели AI

**1. Область чата (верх 65%):**
```cpp
wxTextCtrl* chat_history_;  // wxTE_READONLY | wxTE_MULTILINE | wxTE_RICH2
```
- Пузыри сообщений (цвета: пользователь - #007ACC, AI - #F0F0F0)
- Временные метки
- Поддержка прокрутки
- Копирование текста

**2. Область ввода (средняя 20%):**
```cpp
wxTextCtrl* input_field_;   // wxTE_MULTILINE
wxButton* send_button_;
wxButton* attach_photo_button_;  // Пока неактивна
```
- Многострочный ввод (Enter = отправка, Shift+Enter = новая строка)
- Индикатор отправки (wxGauge или wxActivityIndicator)

**3. Панель управления (нижняя 15%):**
```cpp
wxChoice* language_selector_;    // RU | EN
wxButton* quick_defects_btn_;    // Выпадающий список дефектов
wxButton* settings_btn_;
```

### 6.3 Диалог подтверждения изменений

```cpp
class RecommendationDialog : public wxDialog {
    wxListCtrl* changes_list_;      // Список изменений
    wxTextCtrl* explanation_;       // Объяснение
    wxButton* apply_btn_;
    wxButton* cancel_btn_;
    wxButton* modify_btn_;          // Ручное редактирование
};
```

**Внешний вид:**
```
┌──────────────────────────────────────────────────────┐
│ AI предлагает изменения                    [?] [X]   │
├──────────────────────────────────────────────────────┤
│ Проблема: Расслоение слоев                           │
│ Уверенность: 92%                                     │
├──────────────────────────────────────────────────────┤
│ Параметр          Текущее  →  Новое     Причина      │
│ ───────────────────────────────────────────────────  │
│ ☐ Температура сопла  200°C  →  210°C    [Подробнее]  │
│ ☐ Обдув 1го слоя     100%   →  0%       [Подробнее]  │
├──────────────────────────────────────────────────────┤
│ Советы: Проверьте, что филамент сухой               │
├──────────────────────────────────────────────────────┤
│ [Применить выбранные]  [Отмена]  [Изменить вручную] │
└──────────────────────────────────────────────────────┘
```

### 6.4 Язык и локализация

**Поддерживаемые языки:**
- Русский (RU)
- Английский (EN)

**Механизм локализации:**
```cpp
class I18n {
public:
    static wxString Get(const wxString& key);
    static void SetLanguage(const wxString& lang);
    
private:
    static std::map<wxString, std::map<wxString, wxString>> translations_;
    static wxString current_lang_;
};

// Использование:
wxMessageBox(I18n::Get("dialog.title"));
```

**Файлы переводов:** `resources/i18n/ru.json`, `resources/i18n/en.json`

---

## 7. Соображения по безопасности

### 7.1 Безопасность API

**Хранение ключа HF API:**
```cpp
// НЕ хранить в коде!
// Хранить в: ~/.config/neuro-slicer/config.json (Linux)
//            %APPDATA%/neuro-slicer/config.json (Windows)
//            ~/Library/Application Support/neuro-slicer/config.json (macOS)

class SecureConfig {
public:
    std::string getApiToken();
    void setApiToken(const std::string& token);
    
private:
    std::string config_path_;
    // Можно добавить простое шифрование (base64 или AES)
};
```

**Git:**
- config.json в .gitignore
- Пример конфига: config.json.example

### 7.2 Валидация изменений профиля

```cpp
class ParameterValidator {
public:
    static bool validate(const std::string& param, double value) {
        if (param == "nozzle_temperature") {
            return value >= 150 && value <= 350;
        } else if (param == "fan_speed") {
            return value >= 0 && value <= 100;
        }
        // ... остальные параметры
        return true;
    }
    
    static std::string getErrorMessage(const std::string& param) {
        if (param == "nozzle_temperature") {
            return "Температура должна быть между 150°C и 350°C";
        }
        return "Недопустимое значение параметра";
    }
};
```

### 7.3 Подтверждение пользователя

**Обязательные правила:**
1. Никаких автоматических изменений
2. Предпросмотр перед применением
3. Кнопка "Отмена" всегда доступна
4. Валидация значений перед сохранением

### 7.4 Логирование (безопасное)

```cpp
// Логировать только нечувствительную информацию
spdlog::info("AI request sent: defect_type={}", defect_type);
// НЕ логировать: spdlog::info("API token: {}", token);

spdlog::error("AI request failed: status_code={}", status_code);
// НЕ логировать: spdlog::error("Response body: {}", response);
```

---

## 8. Этапы/вехи разработки

### Этап 1: Подготовка и исследование (Неделя 1)

**Задачи:**
- [ ] Изучить структуру OrcaSlicer (сборка, UI, профили)
- [ ] Настроить CMake проект для C++
- [ ] Подключить зависимости (libcurl, nlohmann/json, spdlog)
- [ ] Создать структурированный JSON-датасет
- [ ] Настроить Hugging Face API доступ
- [ ] Создать тестовый C++ скрипт для API

**Критерии приемки:**
- [ ] Успешная сборка OrcaSlicer из исходников
- [ ] Компилируется тестовый проект с libcurl + nlohmann/json
- [ ] Работает HTTP запрос к HF API из C++
- [ ] Готов JSON с минимум 10 дефектами

**Ресурсы:**
- 1 разработчик C++

### Этап 2: AI Core на C++ (Неделя 2)

**Задачи:**
- [ ] Реализовать NeuroAIClient (HTTP + JSON)
- [ ] Создать PromptBuilder
- [ ] Реализовать ResponseParser
- [ ] Настроить логирование (spdlog)
- [ ] Создать unit тесты

**Критерии приемки:**
- [ ] Успешные HTTP POST запросы к HF API
- [ ] Корректный парсинг JSON ответов
- [ ] AI корректно идентифицирует 80%+ дефектов
- [ ] Время отклика < 10 сек

**Ресурсы:**
- 1 разработчик C++

### Этап 3: ProfileManager на C++ (Неделя 3)

**Задачи:**
- [ ] Реализовать парсер .ini файлов
- [ ] Реализовать парсер .json профилей
- [ ] Создать систему diff-изменений
- [ ] Реализовать валидацию параметров
- [ ] Unit тесты

**Критерии приемки:**
- [ ] Читает все форматы профилей OrcaSlicer
- [ ] Корректно генерирует diff
- [ ] Валидирует значения параметров

**Ресурсы:**
- 1 разработчик C++

### Этап 4: UI на wxWidgets (Недели 4-5)

**Задачи:**
- [ ] Создать NeuroChatPanel
- [ ] Добавить панель в интерфейс OrcaSlicer
- [ ] Реализовать асинхронные запросы (wxThread)
- [ ] Создать RecommendationDialog
- [ ] Добавить локализацию (RU/EN)

**Критерии приемки:**
- [ ] Панель отображается в OrcaSlicer
- [ ] UI не блокируется при запросах
- [ ] Работает переключение языка
- [ ] Диалог рекомендаций функционален

**Ресурсы:**
- 1 разработчик C++/wxWidgets

### Этап 5: Интеграция и тестирование (Неделя 6)

**Задачи:**
- [ ] Интеграция всех компонентов
- [ ] Интеграционное тестирование
- [ ] Тесты на реальных профилях
- [ ] Обработка ошибок (офлайн, лимиты API)
- [ ] Документация

**Критерии приемки:**
- [ ] 90%+ тестов проходят
- [ ] Стабильная работа на Windows/Linux/Mac
- [ ] Документация готова

**Ресурсы:**
- QA инженер
- Документалист

### Этап 6: Будущее (вне MVP)
- [ ] Интеграция LLaVA для анализа фото
- [ ] Сбор фото-дефектов от пользователей
- [ ] Fine-tuning модели
- [ ] Автооптимизация по истории печатей
- [ ] База знаний сообщества

---

## 9. Потенциальные вызовы и решения

### 9.1 Технические вызовы

**Вызов:** Задержки Hugging Face API (модель "засыпает")
- **Решение:** 
  - Индикатор загрузки в UI
  - Таймаут 30 секунд
  - Повторные попытки (retry logic)
- **Долгосрочное:** Платный тариф или кэширование

**Вызов:** Асинхронность в wxWidgets
- **Решение:** Использовать wxThread + wxThreadEvent для обновления UI

**Вызов:** Парсинг разных форматов профилей
- **Решение:** Универсальный парсер с фабричным методом

### 9.2 UX вызовы

**Вызов:** Пользователи могут не доверять AI
- **Решение:** Прозрачность, объяснения, подтверждение

**Вызов:** AI может ошибаться
- **Решение:** Обязательное подтверждение, валидация, логирование

### 9.3 Бизнес-вызовы

**Вызов:** Лимиты бесплатного HF API
- **Решение:** Для MVP достаточно (30k/мес)
- **Оптимизация:** Кэширование в SQLite

---

## 10. Критерии успеха проекта

### Технические метрики
- Точность диагностики: > 80%
- Время отклика: < 10 сек
- Стабильность: < 1% ошибок
- Покрытие: 29+ типов дефектов

### Пользовательские метрики
- Экономия времени: 30+ минут на настройку
- Удовлетворенность: > 4.0/5.0
- Использование: > 50% пользователей

---

## История изменений

| Версия | Дата | Автор | Изменения |
|--------|------|-------|-----------|
| 1.0 | 2026-03-02 | NeuroSlicer Team | Начальная версия (C++ + Python) |
| 1.1 | 2026-03-02 | NeuroSlicer Team | Переписано на чистый C++ |

---

**Статус документа:** ✅ Утвержден для разработки MVP (Pure C++)

**Следующий шаг:** Начало разработки - настройка CMake и зависимостей
