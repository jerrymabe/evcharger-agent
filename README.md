# EV Charger Agent (ChargeGPT)

A conversational AI agent for querying and managing Electric Vehicle (EV) charging station data. Built with Streamlit and LangChain, powered by Google Gemini.

## Features

- **ChargeGPT chat interface** — ask questions about nearby EV chargers in natural language
- **Location-aware** — uses your geolocation to find the nearest chargers
- **Role-based responses** — separate views for Customers and Maintenance Executives
- **Session history** — past conversations are saved and resumable
- **DB Explorer** — interactive dashboard to browse charger data with charts
- **Statistics panel** — quick summaries of charger status, faults, maintenance, and notifications

## Tech Stack

- [Streamlit](https://streamlit.io/) — frontend UI
- [LangChain](https://www.langchain.com/) — LLM orchestration and SQL agent
- [Google Gemini](https://deepmind.google/technologies/gemini/) (`gemini-2.5-flash`) — language model
- [SQLite](https://www.sqlite.org/) — local database
- [GeoPy](https://geopy.readthedocs.io/) — reverse geocoding

## Project Structure

```
├── app.py           # Main Streamlit app (ChargeGPT chat)
├── main.py          # LangChain agent pipeline
├── classes.py       # Pydantic/TypedDict models
├── config.py        # Configuration (model, DB, LLM settings)
├── prompts.py       # All LLM prompt templates
├── sessions.py      # SQLite session management
├── stats.py         # Statistics agent
├── pages/
│   └── dbexplorer.py  # DB Explorer page
└── .streamlit/
    └── config.toml  # Streamlit server config
```

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/jerrymabe/evcharger-agent.git
cd evcharger-agent
```

### 2. Install dependencies

```bash
pip install streamlit langchain langchain-google-genai langchain-community \
            geopy streamlit-geolocation st-copy pydantic
```

### 3. Configure your API key

In `config.py`, set your Google Gemini API key:

```python
API_KEY = "your-gemini-api-key-here"
```

Or use a `.streamlit/secrets.toml` file (recommended, already gitignored):

```toml
[connections.evc_db]
url = "sqlite:///evdatabase.db"
```

### 4. Add your database

Place your `evdatabase.db` SQLite file in the project root. The app expects these tables:
`dp_ast`, `evc_dvc_sts`, `evc_notifications`, `evc_maintenance`, `evc_flt`

### 5. Run the app

```bash
streamlit run app.py
```

The app will be available at `http://localhost:9988`.

## Usage

1. Allow location access when prompted
2. Select your role: **Customer** or **Maintenance Executive**
3. Enter your name to enable session history
4. Ask questions like:
   - *"Which is the nearest EV charger?"*
   - *"Is it operational?"*
   - *"When is the next maintenance here?"*
   - *"Is there any fault with it?"*

## Notes

- API keys should never be committed. Use `config.py` as a template and keep your actual key in an environment variable or `.streamlit/secrets.toml` (gitignored).
- The SQLite `.db` files are gitignored to avoid committing potentially sensitive operational data.
