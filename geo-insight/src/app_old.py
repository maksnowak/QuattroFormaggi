import os
import sys
import traceback

# Add quattroformaggi module to path
# In Databricks Apps, we use relative paths
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

print(f"[DEBUG] Current directory: {current_dir}")
print(f"[DEBUG] Source path: {src_path}")
print(f"[DEBUG] sys.path: {sys.path[:3]}")

import gradio as gr
import pandas as pd
from databricks import sql

from quattroformaggi.BriefingNoteWriter import brief_writer
from quattroformaggi.QueryInterpreter import interpret_query
from quattroformaggi.query_to_sql import filter_humanitarian_data

print("[DEBUG] All imports successful")
print(os.environ)

# Create the main chat pipeline function
async def chat_pipeline(message, history):
    print(f"\n[DEBUG] === Starting chat_pipeline ===")
    print(f"[DEBUG] User message: {message}")
    print(f"[DEBUG] History length: {len(history) if history else 0}")
    
    try:
        # Step 1: Agent 1 interprets the natural language query
        print("[DEBUG] Step 1: Calling interpret_query...")
        agent1_result = await interpret_query(message)
        print(f"[DEBUG] Agent 1 result type: {type(agent1_result)}")
        
        agent_json = agent1_result.model_dump_json()
        print(f"[DEBUG] Agent 1 JSON (first 200 chars): {agent_json[:200]}")

        # Step 2: Fetch and filter data using Databricks SQL Connector
        master_table_path = "unocha.default.master_table"
        print(f"[DEBUG] Step 2: Connecting to Databricks SQL...")
        print(f"[DEBUG] Master table: {master_table_path}")
        
        db_host = os.getenv("DATABRICKS_HOST")
        db_http_path = os.getenv("DATABRICKS_HTTP_PATH")
        db_token = os.getenv("DATABRICKS_TOKEN")
        
        print(f"[DEBUG] DATABRICKS_HOST: {db_host}")
        print(f"[DEBUG] DATABRICKS_HTTP_PATH: {db_http_path}")
        print(f"[DEBUG] DATABRICKS_TOKEN present: {bool(db_token)}")
        
        connection = sql.connect(
            server_hostname=db_host,
            http_path=db_http_path,
            access_token=db_token
        )
        print("[DEBUG] Database connection established")
        
        try:
            print("[DEBUG] Calling filter_humanitarian_data...")
            filtered_df = filter_humanitarian_data(agent_json, connection, master_table_path)
            print(f"[DEBUG] Filtered DataFrame shape: {filtered_df.shape}")
            print(f"[DEBUG] Filtered DataFrame columns: {list(filtered_df.columns)}")
            if filtered_df.empty:
                extended_user_message = message + " Check broader context like other countries in the area (radius of about 500km from the border), simillar context, or broader time period."
                agent1_extended_result = await interpret_query(message)
                agent_json_extended = agent1_extended_result.model_dump_json()
                print(f"[DEBUG] Agent 1 extended response: {agent_json_extended}")
                filtered_df_extended = filter_humanitarian_data(agent_json_extended, connection, master_table_path)
                data_as_csv_string_extended = filtered_df_extended.to_csv(index=False)
                print(f"[DEBUG] Extended CSV string length: {len(data_as_csv_string_extended)} characters")
                agent2_extended_result = await brief_writer(data_as_csv_string_extended, extended_user_message, agent1_extended_result)
                print(f"[DEBUG] Agent 2 extended result length: {len(agent2_extended_result)} characters")
        finally:
            connection.close()
            print("[DEBUG] Database connection closed")
            if filtered_df.empty: 
                if filtered_df_extended.empty:
                    return "The extended search did not find any matches in the Humanitarian Crises Database."
                return agent2_extended_result
        
        # Step 3: Convert the filtered DataFrame
        print("[DEBUG] Step 3: Converting DataFrame to CSV...")
        data_as_csv_string = filtered_df.to_csv(index=False)
        print(f"[DEBUG] CSV string length: {len(data_as_csv_string)} characters")

        # Step 4: Agent 2 generates the Briefing Note based on the data
        print("[DEBUG] Step 4: Calling brief_writer...")
        agent2_result = await brief_writer(data_as_csv_string, message, agent1_result)
        print(f"[DEBUG] Agent 2 result length: {len(agent2_result)} characters")
        
        # Return the generated report to the UI
        print("[DEBUG] === Pipeline completed successfully ===\n")
        return agent2_result
        
    except Exception as e:
        # Graceful error handling for the UI
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Exception occurred: {str(e)}")
        print(f"[ERROR] Traceback:\n{error_traceback}")
        return f"**Pipeline Error:** An error occurred while processing your request: `{str(e)}`\n\n<details><summary>Debug Info</summary>\n\n```\n{error_traceback}\n```\n</details>"

# Configure the Gradio Interface
print("[DEBUG] Configuring Gradio interface...")
demo = gr.ChatInterface(
    fn=chat_pipeline,
    title="Geo-Insight: GapFinder Assistant",
    description="Ask a natural language question about financial gaps in humanitarian crises. The system will query the underlying data and generate a professional Briefing Note for decision support.",
    examples=[
        "Show underfunded food crises in the Sahel since 2022.",
        "Current state of Middle East",
        "History of funding in Africa"
    ]
)
print("[DEBUG] Gradio interface configured")

# Launch the app for Databricks Apps (public access)
if __name__ == "__main__":
    print("[DEBUG] Starting Gradio app launch...")
    demo.launch(share=True, inline=True)
