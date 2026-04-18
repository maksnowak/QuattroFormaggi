def run():
    import asyncio

    from dotenv import load_dotenv

    from quattroformaggi.QueryInterpreter import interpret_query
    from query_to_sql import filter_humanitarian_data

    import pandas as pd

    load_dotenv()

    user_query = "show underfunded food crises in the Sahel since 2022"

    agent1_result = asyncio.run(
        interpret_query(user_query)
    )

    agent_json = agent1_result.model_dump_json()

    master_table_path = "unocha.default.master_table"

    filtered_df = filter_humanitarian_data(agent_json, spark, master_table_path)

    data_as_csv_string = filtered_df.toPandas().to_csv(index=False)

    agent2_result = asyncio.run(
        brief_writer(data_as_csv_string, user_query)
    )

    print(agent2_result)

