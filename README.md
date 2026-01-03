# Enterprise Strategy Synthesis Platform - Autonomous Management Consulting System

**Production-grade multi-agent AI system that generates consulting decks in 90 seconds.**

Transform strategic questions into comprehensive consulting presentations with financial models, market analysis, regulatory assessments, and actionable recommendations.

---

## 🚀 Features

### Multi-Agent Architecture
- **Research Agent**: RAG-powered research with 1000+ case studies, real-time news, financial data
- **Analyst Agent**: Market sizing, Financial modeling
- **Regulatory Agent**: FDI analysis, tax implications, geopolitical risk, compliance roadmap
- **Synthesizer Agent**: Executive summaries, implementation roadmaps, 12-15 slide decks

### Professional Outputs
- 📄 **PDF Decks**: Consulting-grade formatting with embedded charts
- 📊 **PowerPoint**: Editable slides with speaker notes
- 📋 **JSON**: Complete structured data export





## 🏗️ Architecture

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Research Agent  │  
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────────┐
│Analyst │ │ Regulatory │  
│ Agent  │ │   Agent    │
└───┬────┘ └─────┬──────┘
    │            │
    └─────┬──────┘
          ▼
   ┌──────────────┐
   │ Synthesizer  │ 
   │    Agent     │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ PDF/PPT/JSON │
   └──────────────┘
```


---

**Built for strategic decision-making**

*Transform strategic questions into actionable insights in under 90 seconds.*
