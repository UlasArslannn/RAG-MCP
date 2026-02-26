# 🍕 RAG-MCP — AI-Powered Restaurant Review Analyzer

An AI agent that connects to a **restaurant reviews database** via the **Model Context Protocol (MCP)**, allowing you to chat with your data using natural language. Ask questions like *"What do people think about the pizza?"* and get intelligent, context-aware answers.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    docker compose up                     │
│                                                          │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │  MCP Server    │  │  FastAPI App   │  │    Ollama    │ │
│  │  (SSE)         │  │  (Chat API)    │  │   (LLM)     │ │
│  │  Port 8000     │◄─│  Port 8001     │─►│  Port 11434 │ │
│  │  SQLite DB     │  │  LlamaIndex    │  │  llama3.2   │ │
│  └───────────────┘  └───────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

| Bileşen | Açıklama |
|---------|----------|
| **MCP Server** (`scripts/new_server.py`) | SQLite veritabanına SSE üzerinden erişim sağlar. `add_comment` ve `get_comments` tool'larını sunar. |
| **FastAPI App** (`scripts/main.py`) | LlamaIndex FunctionAgent kullanarak kullanıcı mesajlarını işler, gerektiğinde MCP tool'larını çağırır. |
| **Ollama** | `llama3.2` modelini çalıştırarak doğal dil anlama ve yanıt üretme sağlar. |
| **Scraping** (`scripts/scraping.py`) | Google Maps'ten restoran yorumlarını Selenium ile çeker (lokal kullanım). |

## 📁 Proje Yapısı

```
RAG-MCP/
├── scripts/
│   ├── new_server.py      # MCP Server (SQLite + SSE)
│   ├── main.py            # FastAPI Chat API
│   ├── agent_utils.py     # LLM & Agent konfigürasyonu
│   ├── server.py          # LangChain RAG server (CLI)
│   ├── vector.py          # ChromaDB vektör veritabanı
│   └── scraping.py        # Google Maps yorum scraper
├── tests/
│   ├── conftest.py        # Test fixtures
│   ├── test_mcp_server.py # DB operasyon testleri
│   └── test_api.py        # FastAPI endpoint testleri
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml         # Python bağımlılıkları (uv)
├── requirements.txt       # LangChain bağımlılıkları
├── sql.py                 # Örnek veri ekleme scripti
└── reviews.db             # SQLite veritabanı
```

---

## 🐳 Docker ile Kurulum (Önerilen)

Projeyi tek komutla ayağa kaldırın — Python, Ollama veya herhangi bir bağımlılık kurmanıza gerek yok.

### Gereksinimler

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) yüklü ve çalışıyor olmalı
- En az **4GB boş RAM** (LLM modeli için)
- İlk çalıştırmada ~2GB indirme (llama3.2 modeli)

### Adım 1: Repoyu klonlayın

```bash
git clone https://github.com/UlasArslannn/RAG-MCP.git
cd RAG-MCP
```

### Adım 2: Docker Compose ile başlatın

```bash
docker compose up --build
```

Bu komut sırasıyla:
1. ✅ Python Docker image'ını oluşturur
2. ✅ Tüm bağımlılıkları kurar
3. ✅ Ollama servisini başlatır ve `llama3.2` modelini indirir
4. ✅ MCP Server'ı başlatır (port 8000)
5. ✅ FastAPI Chat API'yi başlatır (port 8001)

### Adım 3: Kullanmaya başlayın

Tüm servisler hazır olduğunda:

| Servis | URL |
|--------|-----|
| 💬 Chat API (Swagger UI) | http://localhost:8001/docs |
| 🔧 MCP Server | http://localhost:8000/sse |
| 🤖 Ollama | http://localhost:11434 |

**Chat API'ye mesaj göndermek için:**

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Veritabanındaki tüm yorumları göster"}'
```

Veya Swagger UI'dan: http://localhost:8001/docs → **POST /chat** → Try it out

### Adım 4: Durdurmak için

```bash
docker compose down
```

Veritabanı verilerini de silmek isterseniz:
```bash
docker compose down -v
```

---

## 💻 Lokal Kurulum (Docker'sız)

Docker yerine direkt bilgisayarınızda çalıştırmak isterseniz:

### Gereksinimler

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (paket yöneticisi)
- [Ollama](https://ollama.com/download) (LLM)

### Kurulum

```bash
# 1. Repoyu klonlayın
git clone https://github.com/UlasArslannn/RAG-MCP.git
cd RAG-MCP

# 2. Bağımlılıkları kurun
uv sync

# 3. Ollama'yı başlatın ve modeli indirin
ollama pull llama3.2

# 4. Örnek verileri ekleyin
uv run python sql.py

# 5. MCP Server'ı başlatın (Terminal 1)
uv run python scripts/new_server.py --server_type=sse

# 6. FastAPI'yi başlatın (Terminal 2)
uv run python scripts/main.py
```

---

## 🧪 Testler

```bash
# Testleri çalıştırın
uv run pytest tests/ -v

# Coverage ile çalıştırın
uv run pytest tests/ -v --cov=scripts --cov-report=term-missing
```

### Test Senaryoları

| Test Dosyası | Ne Test Eder | Ollama Gerekli mi? |
|---|---|---|
| `test_mcp_server.py` | DB oluşturma, yorum ekleme/okuma, filtreleme, özel karakterler | ❌ Hayır |
| `test_api.py` | FastAPI endpoint'leri, validation, CORS | ❌ Hayır |

---

## ⚙️ Ortam Değişkenleri

Docker Compose bu değişkenleri otomatik ayarlar. Lokal geliştirmede default değerler kullanılır:

| Değişken | Default | Açıklama |
|----------|---------|----------|
| `MCP_SERVER_URL` | `http://127.0.0.1:8000/sse` | MCP Server SSE endpoint |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API adresi |
| `LLM_MODEL` | `llama3.2` | Kullanılacak LLM modeli |
| `DB_PATH` | `(proje kökü)/reviews.db` | SQLite veritabanı yolu |

---

## 🔄 CI/CD (GitHub Actions)

Her push ve pull request'te otomatik çalışır:

```
Push/PR → 🔍 Lint (ruff) → 🧪 Test (pytest) → 🐳 Docker Build
```

---

## 📝 API Endpoints

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET` | `/` | Health check |
| `POST` | `/chat` | AI agent'a mesaj gönder |
| `POST` | `/reset` | Konuşma geçmişini sıfırla |

### POST /chat

```json
// Request
{
  "message": "En yüksek puanlı yorumları göster",
  "verbose": false
}

// Response
{
  "response": "İşte en yüksek puanlı yorumlar:\n1. Alice (5/5): Margherita pizza was absolutely perfect!...",
  "tool_calls": []
}
```

---

## 📄 Lisans

MIT License — detaylar için [LICENSE](LICENSE) dosyasına bakın.
