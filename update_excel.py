import gspread, os
from dotenv import load_dotenv, set_key
from datetime import datetime

load_dotenv(override=True)

google = gspread.service_account(filename="creds.json")
row = int(os.getenv("EXCEL_ROW"))

spreadsheet = google.open("Budget")

date = datetime.now()
sheet = spreadsheet.worksheet(f'{date.month}-{date.year}')

m_d_y = date.strftime("%m/%d/%Y")
description = "test"
amount = 10
total = float(sheet.acell(f'D{row-1}').value) + amount

sheet.update(f"A{row}", [[m_d_y, description, amount, total]])

set_key(".env", "EXCEL_ROW", str(row + 1))