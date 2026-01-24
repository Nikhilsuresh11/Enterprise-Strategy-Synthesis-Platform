# Version 2 - Agentic Research Platform

Revamped enterprise strategy synthesis platform with:
- 6 specialized agents
- LangGraph orchestration
- Free-tier optimized (Groq, MongoDB, Pinecone, Render)
- Parallel execution
- Validation feedback loops

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run locally
python -m uvicorn app.main:app --reload
```

## Architecture

- **Agents**: 6 specialized agents for company analysis
- **LangGraph**: Workflow orchestration with parallel execution
- **Pinecone**: RAG with built-in inference (no transformers needed)
- **Groq**: Primary LLM (free tier: 14K RPM)
- **MongoDB**: Caching and storage
- **AgentOps**: Monitoring and tracking
