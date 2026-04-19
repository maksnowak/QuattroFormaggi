import os
import asyncio
import importlib
import nest_asyncio  # <-- Rozwiązuje wszystkie problemy z pętlami w Databricks
from dotenv import load_dotenv
from databricks import sql
from databricks.sdk import WorkspaceClient

from quattroformaggi.BriefingNoteWriter import brief_writer
from quattroformaggi import query_to_sql
from quattroformaggi.QueryInterpreter import interpret_query

# Force reload the module to pick up changes
importlib.reload(query_to_sql)
from quattroformaggi.query_to_sql import filter_humanitarian_data

# Aplikujemy łatkę dla Databricks/Jupyter, która pozwala używać asyncio.run()
nest_asyncio.apply()

async def async_run():
    # Załaduj zmienne środowiskowe z pliku .env (jeśli go masz)

    user_query = "show underfunded food crises in the Sahel since 2022"

    # 1. Agent 1 interpretuje zapytanie
    print("Agent 1 pracuje...")
    agent1_result = await interpret_query(user_query)
    agent_json = agent1_result.model_dump_json()

    # 2. Połączenie z Databricks SQL i pobranie danych
    master_table_path = "unocha.default.master_table"
    
    print("Pobieram dane z Databricks SQL...")
    # Get connection parameters from current Databricks context
    connection = sql.connect(
        server_hostname=spark.conf.get("spark.databricks.workspaceUrl"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
    )
    
    try:
        filtered_df = filter_humanitarian_data(agent_json, connection, master_table_path)
    finally:
        connection.close()

    if filtered_df.empty:
        print("Nie znaleziono danych pasujących do zapytania.")
        return

    # 3. Konwersja Pandas DataFrame prosto do CSV
    data_as_csv_string = filtered_df.to_csv(index=False)

    # 4. Agent 2 generuje raport
    print("Agent 2 pisze raport...")
    agent2_result = await brief_writer(data_as_csv_string, agent1_result.interpretation_notes)

    print("\n" + "="*40)
    print("GOTOWY RAPORT")
    print("="*40 + "\n")
    print(agent2_result)


# --- BLOK URUCHOMIENIOWY ---
if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment variable
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not found in environment. "
            "Please set it in your .env file or as an environment variable."
        )
    
    # Dynamically get the first available SQL warehouse
    w = WorkspaceClient()
    warehouses = list(w.warehouses.list())
    if not warehouses:
        raise RuntimeError("No SQL warehouses available. Please create one in the SQL Warehouses UI.")
    warehouse = warehouses[0]
    os.environ["DATABRICKS_HTTP_PATH"] = f"/sql/1.0/warehouses/{warehouse.id}"
    print(f"Using SQL Warehouse: {warehouse.name} (ID: {warehouse.id})")

    # Wywołujemy funkcję w sposób standardowy - skrypt poczeka na zakończenie
    asyncio.run(async_run())
