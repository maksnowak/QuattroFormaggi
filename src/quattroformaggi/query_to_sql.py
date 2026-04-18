import json
from pyspark.sql import functions as F
from pyspark.sql import DataFrame

def filter_humanitarian_data(agent_json_string: str, spark, table_name: str) -> DataFrame:
    """
    Filters the main table based on parameters from the agent's JSON.
    Returns a filtered PySpark DataFrame object.
    """
    # 1. Parse the JSON into a Python dictionary
    try:
        filters = json.loads(agent_json_string)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        # In case of an error, return an empty DataFrame based on the table schema
        return spark.table(table_name).limit(0)

    # 2. Load the table
    df = spark.table(table_name)

    # 3. Dynamically add filtering conditions
    if filters.get("regions"):
        df = df.filter(F.col("country_code").isin(filters["regions"]))

    if filters.get("sectors"):
        df = df.filter(F.col("cluster_code").isin(filters["sectors"]))

    if filters.get("year_range") and len(filters["year_range"]) == 2:
        min_year = filters["year_range"][0]
        max_year = filters["year_range"][1]
        df = df.filter(F.col("year").between(min_year, max_year))

    # 4. Return the filtered DataFrame
    return df