import os
import sys
import traceback
import pandas as pd

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
from quattroformaggi.query_to_articles import filter_articles

print("[DEBUG] All imports successful")
print(os.environ)

# Main chat pipeline function (Logic unchanged)
async def chat_pipeline(message):
    print(f"\n[DEBUG] === Starting chat_pipeline ===")
    print(f"[DEBUG] User message: {message}")
    
    try:
        # Step 1: Agent 1 interprets the natural language query
        print("[DEBUG] Step 1: Calling interpret_query...")
        agent1_result = await interpret_query(message)
        print(f"[DEBUG] Agent 1 result type: {type(agent1_result)}")
        
        agent_json = agent1_result.model_dump_json()
        print(f"[DEBUG] Agent 1 JSON (first 200 chars): {agent_json[:200]}")

        # Step 2: Fetch and filter data using Databricks SQL Connector
        master_table_path = "unocha.default.master_table"
        master_articles_path = "unocha.default.reliefweb_cleaned"
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
            filtered_articles = filter_articles(agent_json, connection, master_articles_path)
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
                # Append extended dataframe to extended result
                df_markdown = "\n\n---\n\n## Data Table\n\n" + filtered_df_extended.to_markdown(index=False)
                return agent2_extended_result + df_markdown
        
        # Step 3: Convert the filtered DataFrame
        print("[DEBUG] Step 3: Converting DataFrame to CSV...")
        data_as_csv_string = filtered_df.to_csv(index=False)
        articles_as_string = filtered_articles.to_csv(index=False)
        print(f"[DEBUG] CSV string length: {len(data_as_csv_string)} characters")
        print(f"[DEBUG] Articles string length: {len(articles_as_string)} characters")

        # Step 4: Agent 2 generates the Briefing Note based on the data
        print("[DEBUG] Step 4: Calling brief_writer...")
        agent2_result = await brief_writer(data_as_csv_string, message, articles_as_string, agent1_result)
        print(f"[DEBUG] Agent 2 result length: {len(agent2_result)} characters")
        
        # Append the filtered DataFrame as a markdown table
        print("[DEBUG] Appending filtered DataFrame to result...")
        # 1. Agregacja (Grupujemy po kraju)
        print_df = filtered_df.groupby("country_code").agg({
            "population": "max", 
            "total_required_funds": "sum", 
            "total_granted_funds": "sum", 
            "severity_index": "max" 
        }).reset_index()



        # 2. DROP - Usunięty, bo agg() i tak zostawia tylko te kolumny, które wymieniliśmy wyżej.
        # Próba usunięcia nieistniejących kolumn rzuciłaby błąd.

        # 3. Formatowanie kolumn (Używamy .map() lub .apply(), bo to są serie danych, nie pojedyncze skalarne wartości)
        print_df['population'] = print_df['population'].map(lambda x: f"{x/1000000:.1f}M")
        print_df['total_required_funds'] = print_df['total_required_funds'].map(lambda x: f"${x/1000000:.1f}M")
        print_df['total_granted_funds'] = print_df['total_granted_funds'].map(lambda x: f"${x/1000000:.1f}M")

        print_df = print_df.rename(columns={
            "country_code": "Country",
            "population": "Population",
            "total_required_funds": "Required Funds",
            "total_granted_funds": "Granted Funds",
            "severity_index": "Severity Index"
        })
        
        # 4. Tabela Markdown (Używamy print_df, czyli tej sformatowanej wersji, a nie filtered_df)
        df_markdown = "\n\n---\n\n## Summary Data Table\n\n" + print_df.to_markdown(index=False)
        final_result = agent2_result + df_markdown
        
        # Return the generated report to the UI
        print("[DEBUG] === Pipeline completed successfully ===\n")
        return final_result
        
    except Exception as e:
        # Graceful error handling for the UI
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Exception occurred: {str(e)}")
        print(f"[ERROR] Traceback:\n{error_traceback}")
        return f"**Pipeline Error:** An error occurred while processing your request: `{str(e)}`\n\n<details><summary>Debug Info</summary>\n\n```\n{error_traceback}\n```\n</details>"

# ==========================================
# CUSTOM UI STYLING & BEHAVIOR
# ==========================================

custom_css = """
/* Force background everywhere to remove dark stripes */
html, body, gradio-app, .gradio-container {
    background-color: #FDFBF7 !important; 
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

/* Force ALL text globally to be dark to prevent bleeding */
html, body, gradio-app, .gradio-container, h1, h2, h3, h4, h5, h6, p, span, div, label, strong, b, em, i {
    color: #111111 !important;
}

/* Center layouts */
.center-container {
    max-width: 800px !important;
    margin: 15vh auto !important;
}

.paper-container {
    max-width: 900px !important;
    margin: 40px auto !important;
}

/* Fix Input Box styling */
textarea {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #CCCCCC !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
}
textarea::placeholder {
    color: #888888 !important;
}

/* ALL BUTTONS: Very light grey background, dark text */
button, .gr-button, .gr-button-primary, .gr-button-secondary {
    background-color: #F3F4F6 !important; /* Lighter grey */
    color: #000000 !important;
    border: 1px solid #D1D5DB !important;
}
button:hover, .gr-button:hover, .gr-button-primary:hover, .gr-button-secondary:hover {
    background-color: #E5E7EB !important; /* Slightly darker on hover */
}

/* SEND BUTTON - custom color */
.send-btn {
    background-color: #6e5353 !important;
    color: #FFFFFF !important;
    border: 1px solid #5a4444 !important;
}

.send-btn:hover {
    background-color: #5a4444 !important;
}

.send-btn:active {
    background-color: #4a3838 !important;
}

/* Fix Examples styling */
.gr-samples button {
    background-color: #FFFFFF !important;
}
.gr-samples button:hover {
    background-color: #F9FAFB !important;
}
.gr-samples > span.label {
    color: #666666 !important;
}

/* Paper view styling - STRICTLY ALL BLACK TEXT */
.paper-box {
    background-color: #FFFFFF !important;
    padding: 60px 80px !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.08) !important;
    border: 1px solid #EAEAEA !important;
    min-height: 800px;
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 16px;
    line-height: 1.6;
}
.paper-box, .paper-box * {
    color: #000000 !important; /* Forces all Markdown elements to be pure black */
}

/* Fix Markdown Code / Inline Code Styling */
.paper-box code, .paper-box pre, code, pre {
    background-color: #F5F5F5 !important; /* Light grey background for code */
    color: #111111 !important;            /* Dark text */
    border: 1px solid #E0E0E0 !important; /* Subtle border */
    border-radius: 4px !important;
    padding: 0.1em 0.3em !important;
    font-family: monospace !important;
}
.paper-box pre {
    padding: 1em !important;
    overflow-x: auto !important;
}
.paper-box pre code {
    border: none !important;
    background-color: transparent !important;
    padding: 0 !important;
}

/* Table Styling - 100% width */
.paper-box table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 1em 0 !important;
}
.paper-box table th, .paper-box table td {
    border: 1px solid #DDDDDD !important;
    padding: 8px 12px !important;
    text-align: left !important;
}
.paper-box table th {
    background-color: #F5F5F5 !important;
    font-weight: bold !important;
}

/* Spinning Wheel loader */
.loader-wrapper {
    text-align: center;
    padding: 40px;
}
.spinner {
    border: 5px solid #EAEAEA;
    border-top: 5px solid #666666;
    border-radius: 50%;
    width: 60px;
    height: 60px;
    animation: spin 1s linear infinite;
    margin: 0 auto;
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
.loader-text {
    margin-top: 20px;
    font-size: 16px;
}
.loader-text, .loader-text * {
    color: #000000 !important; /* Explicitly dark text for the loading message */
}

/* Button Layout for Results */
.action-buttons {
    display: flex !important;
    justify-content: flex-end !important;
    gap: 15px !important;
    margin-bottom: 20px !important;
}

/* ACTION BUTTONS - white text */
.action-buttons button {
    color: #FFFFFF !important;
}

/* Mobile Responsive Styles */
@media screen and (max-width: 768px) {
    .center-container {
        max-width: 95% !important;
        margin: 5vh auto !important;
    }
    
    .paper-container {
        max-width: 95% !important;
        margin: 20px auto !important;
    }
    
    .paper-box {
        padding: 30px 20px !important;
        font-size: 14px !important;
    }
    
    .action-buttons {
        flex-direction: column !important;
        gap: 10px !important;
    }
    
    .action-buttons button {
        width: 100% !important;
    }
    
    /* Mobile table styles - scrollable container */
    .paper-box table {
        display: block !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        font-size: 12px !important;
    }
    
    .paper-box table th, .paper-box table td {
        padding: 6px 8px !important;
        font-size: 12px !important;
    }
}

/* Print specific styles */
@media print {
    body, .gradio-container, html { background-color: #FFFFFF !important; }
    .action-buttons, footer, .gr-button { display: none !important; }
    .paper-container { max-width: 100% !important; margin: 0 !important; }
    .paper-box { 
        box-shadow: none !important; 
        border: none !important; 
        padding: 0 !important; 
    }
}
"""

print("[DEBUG] Configuring custom Gradio layout...")

with gr.Blocks(css=custom_css, theme=gr.themes.Default(neutral_hue="slate")) as demo:
    
    # ---------------------------
    # VIEW 1: Input / Search
    # ---------------------------
    with gr.Column(visible=True, elem_classes=["center-container"]) as search_view:
        gr.Markdown(
            "<h1 style='text-align: center;'>Geo-Insight Assistant</h1>"
            "<p style='text-align: center; color: #555555 !important; margin-bottom: 30px;'>Ask a natural language question about financial gaps in humanitarian crises. The system will query the underlying data and generate a professional Briefing Note.</p>"
        )
        
        with gr.Row():
            user_input = gr.Textbox(
                placeholder="E.g., Show underfunded food crises in the Sahel since 2022...",
                show_label=False,
                scale=5,
                container=False
            )
            submit_btn = gr.Button("Send", scale=1, elem_classes=["send-btn"])
            
        gr.Examples(
            examples=[
                "Show underfunded food crises in the Sahel since 2022.",
                "Current state of Middle East.",
                "History of funding in Africa."
            ],
            inputs=user_input
        )

    # ---------------------------
    # VIEW 2: Loading State
    # ---------------------------
    with gr.Column(visible=False, elem_classes=["center-container"]) as loading_view:
        gr.HTML("""
            <div class="loader-wrapper">
                <div class="spinner"></div>
                <div class="loader-text">
                    <strong>Processing Query...</strong><br/>
                    Retrieval could take 30-40s. Please wait.
                </div>
            </div>
        """)

    # ---------------------------
    # VIEW 3: Results (Paper & Buttons)
    # ---------------------------
    with gr.Column(visible=False, elem_classes=["paper-container"]) as result_view:
        with gr.Row(elem_classes=["action-buttons"]):
            new_query_btn = gr.Button("New Query")
            save_pdf_btn = gr.Button("Save as PDF")
            
        output_paper = gr.Markdown("", elem_classes=["paper-box"])

    # ---------------------------
    # Event Handlers
    # ---------------------------
    def transition_to_loading():
        return [
            gr.update(visible=False), # Hide search
            gr.update(visible=True),  # Show loader
            gr.update(visible=False)  # Hide result
        ]
        
    async def run_pipeline_and_show(msg):
        result = await chat_pipeline(msg)
        return [
            gr.update(visible=False), # Hide loader
            gr.update(visible=True),  # Show result
            result                    # Populate paper
        ]
        
    def reset_app():
        return [
            gr.update(visible=True),  # Show search
            gr.update(visible=False), # Hide loader
            gr.update(visible=False), # Hide result
            gr.update(value="")       # Clear text input
        ]

    # Triggering the pipeline (Button click or Enter key)
    submit_btn.click(
        fn=transition_to_loading, outputs=[search_view, loading_view, result_view]
    ).then(
        fn=run_pipeline_and_show, inputs=[user_input], outputs=[loading_view, result_view, output_paper]
    )
    
    user_input.submit(
        fn=transition_to_loading, outputs=[search_view, loading_view, result_view]
    ).then(
        fn=run_pipeline_and_show, inputs=[user_input], outputs=[loading_view, result_view, output_paper]
    )

    # Action buttons
    new_query_btn.click(
        fn=reset_app, outputs=[search_view, loading_view, result_view, user_input]
    )
    
    # Save as PDF leverages the browser print function + print specific CSS
    save_pdf_btn.click(
        fn=None, inputs=None, outputs=None, js="() => { window.print(); }"
    )

print("[DEBUG] Gradio interface configured")

# Launch the app for Databricks Apps (public access)
if __name__ == "__main__":
    print("[DEBUG] Starting Gradio app launch...")
    demo.launch(share=True, inline=True)
