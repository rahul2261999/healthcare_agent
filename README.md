# Healthcare Appointment Agent ★

A reference implementation of an appointment-focused **LangGraph** agent. The agent is designed to work locally with the `langgraph dev` development server so you can iterate quickly and inspect every run in the Studio UI.

---

## ✨ Features

* Appointment management workflows (list, book, confirm, cancel)
* Strict tool-calling guardrails – zero hallucinated function names
* State managed with [`TypedDict`](https://docs.python.org/3/library/typing.html#typing.TypedDict) for safety
* Runs on **Claude 3.5 Haiku** by default (Anthropic) – swap the model easily
* Batteries-included local dev workflow via `langgraph-cli[inmem]`

> **Scope** The agent deliberately **does not** access prescriptions or medical records. Non-appointment requests are politely declined without additional recommendations, per the system prompt.

---

## ⚡ Quick start (5 steps)

1. **Clone & enter the project**  
   ```bash
   git clone https://github.com/<your-org>/healthcare_agent.git
   cd healthcare_agent
   ```
2. **Create a Python 3.12+ virtualenv**  
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```
3. **Install deps** (editable mode for hot-reloading):  
   ```bash
   pip install -e .            # project code
   pip install "langgraph-cli[inmem]"  # local dev server
   ```
4. **Add API keys**  
   Create a `.env` file at the repo root (ignored by Git) with at least:
   ```dotenv
   # Needed by langchain-anthropic
   ANTHROPIC_API_KEY="sk-..."
   # Optional – enable Mistral fallback
   MISTRAL_API_KEY="..."
   # Enable LangSmith tracing (optional)
   # LANGCHAIN_TRACING_V2=true
   # LANGCHAIN_API_KEY="..."
   ```
5. **Launch the dev server**  
   ```bash
   langgraph dev               # reads ./langgraph.json automatically
   ```
   The server prints two URLs:
   * **API** `http://127.0.0.1:2024` – REST interface
   * **Studio UI** `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

   Hot-reloading is on by default, so any code change or prompt tweak takes effect instantly.

---

## 🗺️ Repository overview

```
healthcare_agent/
│── langgraph.json      # declares the graph entry-point & env file
│── main.py             # simple hello – not used by the agent
│── pyproject.toml      # dependencies & package metadata
│── src/                # all runtime code lives here
└── README.md           # you are here
```

Key modules:
* `src/agents/agent.py` – builds and compiles the LangGraph graph.
* `src/agents/state.py` – source-of-truth schema for the agent's state.
* `src/verticals/provider/tools/` – the appointment tool implementations.
* `src/verticals/provider/prompts/prompts.py` – the **system prompt** used by the agent.

---

## 🏃‍♂️ Running the agent

With the dev server running you can create a **Run** from the Studio UI or via cURL:

```bash
curl -X POST http://127.0.0.1:2024/v1/threads \
     -H "Content-Type: application/json" \
     -d '{
           "graph": "appointment_agent",
           "state": {
             "conversation_channel": "web",
             "welcome_message": "Hi! I\'m Alex, here to help you with your appointments. How can I assist you today?",
             "otp_sent": false,
             "customer": {
               "id": "CUST-1001",
               "name": "Jane Smith",
               "phone_number": "+919876543210",
               "dob": "22-07-2000"
             },
             "agent_branding": {
               "name": "Alex Johnson",
               "persona": "A friendly and efficient appointment coordinator who helps customers book, confirm, reschedule, or cancel their appointments with ease. Always clear, helpful, and focused on customer convenience.",
               "tone": "Helpful and courteous"
             },
             "messages": [
               { "type": "human", "content": "hey" }
             ]
           }
         }'
```

After posting, watch the run in the Studio UI to see tool calls and intermediate steps.

### 📄 Example state file

Prefer a ready-made file? Grab `src/mock/sample_state.json` (added to the repo) and pass it directly:

```bash
curl -X POST http://127.0.0.1:2024/v1/threads \
     -H "Content-Type: application/json" \
     --data-binary @src/mock/sample_state.json
```

The file contains the canonical state object shown above so you can test the agent immediately.

View it directly: [`src/mock/sample_state.json`](src/mock/sample_state.json)

---

## 🔄 Common dev commands

| Task                            | Command                                    |
|---------------------------------|--------------------------------------------|
| Start local dev server          | `langgraph dev`                            |
| Lint code with Ruff             | `ruff check src`                           |
| Fix lint issues automatically   | `ruff check src --fix`                     |
| Export dependency lockfile      | `pip-compile -o uv.lock pyproject.toml`    |
| Run unit tests (if added)       | `pytest -q`                                |

---

## 🛠️ Swapping the LLM

`src/agents/agent.py` binds the Anthropic client:

```python
llm = ChatAnthropic(model_name="claude-3-5-haiku-latest", temperature=0.0)
```

Change to `ChatMistralAI` (uncommented in code) or any other `langchain` chat model – just remember to set the corresponding API key in `.env`.

---

## 🤝 Contributing

1. Fork & create a feature branch
2. Follow the quick-start above
3. Ensure `ruff` passes (`ruff check src`)
4. Open a PR – thank you!

---

## 📜 License

This repository is distributed under the MIT License. See `LICENSE` (if present) for details.
