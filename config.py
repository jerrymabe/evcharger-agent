# Window for rephrasing
MAX_WINDOW = 3

# SQL Database
DB_CONNECTION_STRING = "sqlite:///evdatabase.db"
DB_NAME = "evdatabase.db"
DB_TABLES = ["dp_ast","evc_dvc_sts","evc_notifications","evc_maintenance","evc_flt"]
TOP_K_TO_QUERY = 2

# LLM
LLM_PROVIDER_TO_USE = "GOOGLE" # "OPENAI"
API_KEY = "" # "sk-..."
LLM_MODEL_PROVIDER = "google_genai" # "openai"
LLM_MODEL = "gemini-2.5-flash" # "gpt-4.1"

# LLM fine-tuning
LLM_TEMPERATURE = 0.7
LLM_MAX_RETRIES = 3
LLM_MAX_OUT_TOKENS = 1024
LLM_TIMEOUT = 30