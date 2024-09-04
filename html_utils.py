def save_result_to_html(task_id, scade_response):
    result_data = scade_response.get("result", {}) or scade_response.get("data", {}).get("node_settings", {}).get(Config.START_NODE_ID, {}).get("data", {})

    from_ = result_data.get("from", "N/A")
    subject = result_data.get("subject", "N/A")
    body = result_data.get("body", "N/A")
    date = result_data.get("date", "N/A")

    # Создание HTML-контента с CSS-стилями строгого дизайна
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Scade Result - Task ID: {task_id}</title>
        <style>
            body {{
                font-family: "Helvetica Neue", Arial, sans-serif;
                background-color: #ffffff;
                margin: 40px;
                padding: 0;
                color: #333;
            }}
            h1 {{
                color: #333;
                font-size: 22px;
                border-bottom: 2px solid #000;
                padding-bottom: 10px;
                margin-bottom: 30px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            p {{
                font-size: 16px;
                line-height: 1.6;
                margin-bottom: 10px;
                color: #555;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                border: 1px solid #e0e0e0;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                background-color: #f9f9f9;
            }}
            .info {{
                border: 1px solid #ccc;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #fdfdfd;
            }}
            .label {{
                font-weight: bold;
                display: inline-block;
                width: 100px;
                text-transform: uppercase;
                color: #333;
                margin-right: 10px;
                border-right: 2px solid #333;
                padding-right: 10px;
            }}
            .body {{
                background-color: #fdfdfd;
                border: 1px solid #ccc;
                padding: 15px;
                white-space: pre-wrap;
                word-wrap: break-word;
                font-family: monospace;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Scade Task Result</h1>
            <div class="info">
                <p><span class="label">Task ID:</span> {task_id}</p>
                <p><span class="label">From:</span> {from_}</p>
                <p><span class="label">Subject:</span> {subject}</p>
                <p><span class="label">Date:</span> {date}</p>
            </div>
            <div class="body">
                {body}
            </div>
        </div>
    </body>
    </html>
    """

    filename = f"scade_result_{task_id}.html"
    with open(filename, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)

    print(f"Result saved to {filename}")
    return html_content
