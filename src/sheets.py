import gspread
import json, os, io, csv
from groq import Groq
from src.prompts import RAG_ANSWER_PROMPT


def get_worksheet():
    #Authentication and fetching 
    sa_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    gc = gspread.service_account_from_dict(sa_info)
    sheet = gc.open(os.environ["GOOGLE_SHEET_NAME"])
    return sheet.sheet1


def fetch_recent_orders() -> str:
    #last 500 orders
    ws = get_worksheet()
    all_values = ws.get_all_values()

    if not all_values:
        return "No Orders found in the database"
    
    headers = all_values[0]

    #get the last 500 rows (excluding headers)
    recent_rows = all_values[1:][-500:]
    #combine headers and recent rows
    data_to_format = [headers] + recent_rows

    #convert list to CSV string for LLM (easier for it to read)
    
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerows(data_to_format)
    return output.getvalue()


def answer_question(transcript:str)-> str:
    #passing the question and sheet to llama

    context = fetch_recent_orders()

    #producing a natural answer from sheet data

    client = Groq()
    response = client.chat.completions.create(
        model = "llama-3.3-70b-versatile",
        messages= [
            {
                "role":"user",
                "content":RAG_ANSWER_PROMPT.format(
                    context = context ,
                    question = transcript,
                )
            }
        ] ,
        temperature=0.3 ,
    )

    return response.choices[0].message.content
    



