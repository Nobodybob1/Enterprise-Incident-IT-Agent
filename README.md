# Enterprise Incident IT Agent

An AI agent for IT incident response, with a human approval step before it takes any action. You describe an incident in plain English. The agent works out which service is affected, checks the service's status, pulls up the relevant runbooks and similar past tickets, and asks Claude to propose a fix. It then **pauses for your approval** before it "executes" anything.

Built with [LangGraph](https://github.com/langchain-ai/langgraph), [Claude](https://www.anthropic.com/) (Anthropic API), [Voyage AI](https://www.voyageai.com/) embeddings and a local [Qdrant](https://qdrant.tech/) vector store.

> **Note:** This is a learning/demo project. Service status comes from mock data, and the "execute" step only simulates a restart. Nothing real is ever touched.

## How it works

Every incident you report goes through a linear LangGraph pipeline:

```
triage ──► diagnose ──► retrieve ──► propose ──► await_approval ──► execute_action
```

| Step | What it does |
|---|---|
| **triage** | Claude maps your message to one known service (`nginx`, `database`, `auth-service`, `payment-gateway`), or to `unknown` if none match. |
| **diagnose** | Looks up the service's current status, CPU and last restart (mocked in `tools/mock_tools.py`). |
| **retrieve** | RAG step. It embeds your message plus the live status (e.g. `"auth is slow" degraded CPU 91%`) and searches Qdrant for the most relevant runbooks and past tickets. The search only returns tickets for the service triage identified. |
| **propose** | Claude writes a concise fix based on the retrieved context and the live status. Runbook steps take priority over past tickets. |
| **await_approval** | The graph pauses (`interrupt()`) and asks you yes/no. |
| **execute_action** | Simulates the action if you approved, or cancels it and flags the incident for human review. |

All the steps share one `IncidentState` dictionary (`graph/state.py`). Each step reads from it and adds its own output. An `InMemorySaver` checkpointer stores the paused run under a per-incident `thread_id`, so the graph can resume at the same point after you answer.

### Retrieval details

- **Runbooks** (`data/runbooks/*.md`) are organized by symptom rather than by service, so every search can return them.
- **Past tickets** (`data/incidents.json`) each belong to one service. A search only returns tickets for the service triage detected. If the service is `unknown`, the search returns runbooks only.
- The search returns the top 3 matches by cosine similarity and drops any match scoring below `0.3`.

## Project structure

```
.
├── app.py                  # Interactive CLI: type an incident, approve or reject the fix
├── requirements.txt        # Python dependencies
├── graph/
│   ├── state.py            # IncidentState: the shared state schema
│   ├── nodes.py            # The six workflow nodes
│   └── workflow.py         # Builds and compiles the LangGraph (also runnable as a demo)
├── rag/
│   ├── ingest.py           # Embeds runbooks + tickets into the local Qdrant store
│   └── retrieve.py         # Filtered semantic search over that store
├── tools/
│   └── mock_tools.py       # Mock service-status lookup
└── data/
    ├── incidents.json      # Past incident tickets
    └── runbooks/           # Markdown runbooks (disk full, high CPU, unresponsive service)
```

## Setup

**Requirements:** Python 3.10+, an Anthropic API key and a Voyage AI API key.

1. Clone the repository and create a virtual environment:

   ```bash
   git clone https://github.com/Nobodybob1/Enterprise-Incident-IT-Agent.git
   cd Enterprise-Incident-IT-Agent
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:

   ```env
   ANTHROPIC_API_KEY=your-anthropic-key
   VOYAGE_API_KEY=your-voyage-key
   ```

4. Build the vector store. Run this once, and again whenever you change the runbooks or tickets:

   ```bash
   python -m rag.ingest
   ```

   This creates a local `qdrant_data/` folder. The folder is git-ignored.

## Usage

Start the interactive agent:

```bash
python app.py
```

Example session (placeholder output):

```
IT Incident Agent
Describe an incident (or type 'quit' to exit).

Incident: auth-service seems really slow and unresponsive
[Triage] Detected service: auth-service
[Diagnose] Tool result: {'service': 'auth-service', 'status': 'degraded', 'cpu_percent': 91, ...}
[Retrieve] Search query used: '...'
[Retrieve] Sources used: [('runbook', 'high_cpu_usage.md', 0.6), ...]

<Claude's proposed fix>

Approve the proposed action for auth-service?
Your answer (yes/no): yes

[MOCK ACTION] Restarting auth-service... done (simulated).
```

Type `yes`, `y` or `approve` to approve. Any other answer cancels the action.

Other entry points:

- `python -m graph.workflow` runs a single hardcoded demo incident.
- `python -m rag.retrieve` runs a manual retrieval test.

## Customizing

- **Add a runbook:** drop a new `.md` file into `data/runbooks/`, then rerun the ingest step.
- **Add past tickets:** append entries to `data/incidents.json` with the fields `ticket_id`, `service`, `date`, `title`, `description` and `resolution`. Then rerun the ingest step.
- **Add a service:** add it to `MOCK_SERVICES` in `tools/mock_tools.py`. Triage picks up new services automatically.
- **Change the model:** edit `MODEL` in `graph/nodes.py`.

## Limitations and possible next steps

- **Mock data only.** Replace `check_service_status` with calls to a real monitoring API (Prometheus, Datadog, etc.).
- **The execute step always simulates a restart,** whatever Claude actually proposed. A next step would be to have Claude return a structured action (e.g. `restart`, `rollback` or `scale_out`) and execute that.
- **No branch for unknown services.** If triage returns `unknown`, the pipeline still runs to the end. A conditional edge after triage could stop early with a helpful message.
- **In-memory checkpointing.** A paused run is lost if the process restarts. A database-backed checkpointer (e.g. SQLite or Postgres) would let approvals survive a restart.
- **One chunk per document.** This works for short runbooks. Longer documents should be split into smaller chunks before embedding.
