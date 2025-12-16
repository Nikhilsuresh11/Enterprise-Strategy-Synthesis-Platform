# Stratagem AI - Autonomous Management Consulting System

**Production-grade multi-agent AI system that generates McKinsey-quality consulting decks in <90 seconds.**

Transform strategic questions into comprehensive consulting presentations with financial models, market analysis, regulatory assessments, and actionable recommendations.

---

## 🚀 Features

### Multi-Agent Architecture
- **Research Agent**: RAG-powered research with 1000+ case studies, real-time news, financial data
- **Analyst Agent**: Market sizing (TAM/SAM/SOM), financial modeling, DCF valuation, Porter's Five Forces
- **Regulatory Agent**: FDI analysis, tax implications, geopolitical risk, compliance roadmap
- **Synthesizer Agent**: Executive summaries, implementation roadmaps, 12-15 slide decks

### Professional Outputs
- 📄 **PDF Decks**: Consulting-grade formatting with embedded charts
- 📊 **PowerPoint**: Editable slides with speaker notes
- 📋 **JSON**: Complete structured data export

### Performance
- ⚡ **Sub-90 second** end-to-end pipeline
- 🔄 **Parallel execution** of Analyst + Regulatory agents
- 💾 **Intelligent caching** for faster repeated queries

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI, LangGraph |
| **LLMs** | Groq (Llama 3.3 70B) |
| **Vector DB** | Pinecone (Serverless) |
| **Database** | MongoDB Atlas |
| **Charts** | Plotly |
| **PDF/PPT** | ReportLab, python-pptx |
| **Deployment** | Render |

---

## 📦 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB Atlas account
- Pinecone account
- Groq API key

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/stratagem-ai.git
cd stratagem-ai

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Add your API keys to .env
```

### Environment Variables

Create `.env` file:

```bash
# LLM
GROQ_API_KEY=your_groq_api_key

# Databases
MONGODB_URI=mongodb+srv://...
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=stratagem-rag

# Optional
NEWSAPI_KEY=your_newsapi_key
LOG_LEVEL=INFO
```

### Initialize Databases

```bash
# Create MongoDB collections
python scripts/setup_db.py

# Create Pinecone index
python scripts/create_pinecone_index.py

# Ingest RAG data
python scripts/ingest_rag.py
```

### Run Server

```bash
uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

---

## 🎯 Usage

### Submit Analysis Request

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Zomato",
    "industry": "Food Delivery",
    "strategic_question": "Should Zomato expand to Saudi Arabia?",
    "analysis_type": "expansion"
  }'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "progress": 0,
  "created_at": "2024-12-15T19:00:00Z"
}
```

### Check Status

```bash
curl http://localhost:8000/api/v1/status/{job_id}
```

### Get Results

```bash
curl http://localhost:8000/api/v1/results/{job_id}
```

### Download Files

```bash
# PDF
curl http://localhost:8000/api/v1/download/{job_id}/pdf -O

# PowerPoint
curl http://localhost:8000/api/v1/download/{job_id}/pptx -O

# JSON
curl http://localhost:8000/api/v1/download/{job_id}/json -O
```

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze` | Submit analysis request |
| `GET` | `/api/v1/status/{job_id}` | Check analysis status |
| `GET` | `/api/v1/results/{job_id}` | Get completed results |
| `GET` | `/api/v1/download/{job_id}/{format}` | Download PDF/PPT/JSON |
| `GET` | `/health` | Health check |

---

## 🏗️ Architecture

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Research Agent  │  (10s) - RAG + External Data
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────────┐
│Analyst │ │ Regulatory │  (Parallel, ~10s each)
│ Agent  │ │   Agent    │
└───┬────┘ └─────┬──────┘
    │            │
    └─────┬──────┘
          ▼
   ┌──────────────┐
   │ Synthesizer  │  (15s) - Final Deck
   │    Agent     │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ PDF/PPT/JSON │
   └──────────────┘
```

**Total Time**: ~35-45 seconds (target: <90s)

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Test specific components
python tests/test_research_agent.py
python tests/test_analyst_agent.py
python tests/test_regulatory_agent.py
python tests/test_orchestration.py
python tests/test_deck_generation.py
```

---

## 🚀 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guide.

### Quick Deploy to Render

1. Push code to GitHub
2. Connect repository to Render
3. Configure environment variables
4. Deploy!

```bash
git push origin main  # Auto-deploys if connected
```

---

## 📈 Performance Benchmarks

| Component | Target | Actual |
|-----------|--------|--------|
| Research Agent | <30s | ~10s |
| Analyst Agent | <60s | ~8s |
| Regulatory Agent | <60s | ~4s |
| Synthesizer | <10s | ~3s |
| **Total Pipeline** | **<90s** | **~25s** ✅ |

---

## 🎨 Sample Output

### Executive Summary
- Clear recommendation (Proceed/Decline/Conditional)
- Confidence score
- 3 supporting points
- 3 key risks
- Expected impact & timeline

### Slide Deck (12-15 slides)
1. Title Slide
2. Executive Summary
3. Market Overview
4. Market Sizing (TAM/SAM/SOM)
5. Competitive Position
6. Unit Economics
7. Financial Projections
8. Scenario Analysis
9. Regulatory Assessment
10. Risk Matrix
11. Implementation Roadmap
12. Next Steps

---

## 🔧 Development

### Project Structure

```
stratagem-ai/
├── app/
│   ├── agents/          # 4 agents (Research, Analyst, Regulatory, Synthesizer)
│   ├── services/        # LLM, RAG, DB, Charts, Deck generation
│   ├── routers/         # FastAPI endpoints
│   ├── models/          # Pydantic schemas
│   ├── workflows/       # LangGraph orchestration
│   └── utils/           # Helpers, logging
├── tests/               # Comprehensive test suite
├── scripts/             # Setup scripts
├── outputs/             # Generated decks
└── requirements.txt
```

### Adding New Features

1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit PR

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

---

## 📞 Support

For issues or questions:
- Open a GitHub issue
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
- Review logs for debugging

---

## 🎯 Roadmap

### Completed ✅
- [x] Multi-agent architecture
- [x] RAG system with case studies
- [x] Financial modeling & market sizing
- [x] Regulatory analysis
- [x] PDF/PPT generation
- [x] Deployment configuration

### Future Enhancements
- [ ] Email delivery of decks
- [ ] Webhook notifications
- [ ] Analytics dashboard
- [ ] React frontend UI
- [ ] Multi-tenancy
- [ ] Authentication & authorization
- [ ] Advanced caching strategies
- [ ] Real-time collaboration

---

**Built with ❤️ for strategic decision-making**

*Transform strategic questions into actionable insights in under 90 seconds.*
