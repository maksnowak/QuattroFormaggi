import json
import pandas as pd
from databricks import sql

def filter_articles(agent_json_string: str, connection, table_name: str) -> pd.DataFrame:
    """
    Filtruje tabelę na podstawie parametrów z agenta JSON.
    Zwraca przefiltrowany obiekt Pandas DataFrame.
    """
    # 0. Zabezpieczenie przed SQL Injection dla nazwy tabeli (np. akceptuje "schema.table_name")
    if not table_name.replace('_', '').replace('.', '').isalnum():
        raise ValueError("Nieprawidłowa nazwa tabeli")

    # 1. Parsowanie JSON do słownika Python
    try:
        filters = json.loads(agent_json_string)
    except json.JSONDecodeError as e:
        print(f"Błąd parsowania JSON: {e}")
        # W przypadku błędu odpytujemy z warunkiem WHERE 1=0, aby zwrócić pusty DataFrame, ale zachować schemat (kolumny)
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name} WHERE 1=0")
            columns = [desc[0] for desc in cursor.description]
            return pd.DataFrame(columns=columns)

    # 2. Inicjalizacja zapytania i parametrów
    query = f"SELECT * FROM {table_name} WHERE 1=1"
    params = []

    # 3. Dynamiczne budowanie warunków filtrowania z użyciem parametryzacji (?), aby uniknąć SQL Injection
    if filters.get("regions"):
        regions = filters["regions"]
        # Tworzy ciąg "?, ?, ?" dopasowany do długości listy
        placeholders = ', '.join(['?'] * len(regions))
        query += f" AND country IN ({placeholders})"
        params.extend(regions)

    if filters.get("sectors"):
        sectors = filters["sectors"]
        placeholders = ', '.join(['?'] * len(sectors))
        query += f" AND sector_code IN ({placeholders})"
        params.extend(sectors)

    query+=" LIMIT 20"

    # 4. Wykonanie zapytania i zwrócenie wyników jako Pandas DataFrame
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        # Fetch all rows and column names
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        # Convert to Pandas DataFrame
        return pd.DataFrame(rows, columns=columns)
