# NeuroSlicer (Python)

Python-версия ассистента для troubleshooting 3D-печати с опорой на базу кейсов и интеграцию с Hugging Face (`openai/gpt-oss-120b`).

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Токен Hugging Face

Храните токен только в переменных окружения:

```bash
export HF_TOKEN="hf_..."
export HF_MODEL_ID="openai/gpt-oss-120b"
# optional: custom endpoint override
# export HF_ENDPOINT="https://router.huggingface.co/hf-inference/models/openai/gpt-oss-120b"
```

## Запуск CLI

### 1) Диагностика с seed-базой

```bash
neuroslicer "Слои расслаиваются, деталь ломается по слоям"
```

### 2) Диагностика с markdown-базой из локального troubleshooting-репозитория

По умолчанию CLI сначала пытается автоматически найти guide в стандартных папках проекта:
- `data/3D-printing-troubleshooting-guide`
- `data/troubleshooting-guide`
- `3D-printing-troubleshooting-guide`
- `troubleshooting-guide`

Можно явно задать путь:

```bash
neuroslicer "Нити между стенками" --kb-markdown-dir /path/to/3D-printing-troubleshooting-guide
```

Или через переменную окружения:

```bash
export TROUBLESHOOTING_GUIDE_DIR="/path/to/3D-printing-troubleshooting-guide"
```

Если guide не найден, используется `data/troubleshooting_seed.json`.

### 3) Использование Hugging Face API (gpt-oss-120b)

Если `HF_TOKEN` задан, нейросетевой анализ включается автоматически (через `router.huggingface.co`).
Если HF временно недоступен, приложение автоматически перейдёт в fallback без падения.

```bash
neuroslicer "Плохая адгезия первого слоя"
```

Отключить нейросеть (только retrieval fallback):

```bash
neuroslicer "Плохая адгезия первого слоя" --no-hf
```

### 4) Применение рекомендаций к профилю OrcaSlicer

```bash
neuroslicer "Слои расслаиваются" --profile-in profile.json --profile-out profile_patched.json
```

Поддерживаются входные форматы профиля: `.json`, `.ini`.

### 5) Предпросмотр без записи профиля (dry-run)

```bash
neuroslicer "Слои расслаиваются" --profile-in profile.json --profile-out profile_patched.json --dry-run --show-kb-source
```

`--dry-run` покажет рекомендуемые `profile_changes`, но не сохранит файл.
`--show-kb-source` добавит в JSON-ответ поле `kb_source` с фактическим источником знаний.

## Что реализовано сейчас

- Загрузка кейсов из JSON и markdown.
- Retrieval-диагностика по симптомам на BM25 + overlap bonus + RU/EN синонимы.
- Нейросетевой анализ через Hugging Face (`openai/gpt-oss-120b`) с контекстом из troubleshooting guide и JSON-ответом.
- Генерация profile diff-рекомендаций и запись обновленного профиля.
