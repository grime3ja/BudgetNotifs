import gspread, os, json
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from zoneinfo import ZoneInfo
from gspread_formatting import *

class handler(BaseHTTPRequestHandler):
    def respond(self):
        response = json.dumps({"status": "ok"})
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode())

    def get_last_row(self, sheet):
        return len(sheet.get_all_values())

    def prev_ending(self, spreadsheet):
        prev_sheet = spreadsheet.worksheets()[-1]
        row = self.get_last_row(prev_sheet)
        return prev_sheet.cell(row, 4).value
    
    def create_worksheet(self, spreadsheet, date: datetime):
        prev_month_ending_bal = self.prev_ending(spreadsheet)

        spreadsheet.add_worksheet(f'{date.month}-{date.year}', 1, 1)
        sheet = spreadsheet.worksheet(f'{date.month}-{date.year}')
        sheet.append_rows([["Checking", "", "", "", "", "Savings", "", "", ""],
                           ["Date", "Description", "Amount", "Total", "", "Date", "Description", "Amount", "Total"]])
        sheet.merge_cells("A1:D1")
        sheet.merge_cells("F1:I1")

        format_cell_range(sheet, "A1:D1", CellFormat(horizontalAlignment="CENTER", verticalAlignment="MIDDLE"))
        format_cell_range(sheet, "F1:I1", CellFormat(horizontalAlignment="CENTER", verticalAlignment="MIDDLE"))

        sheet.append_row([date.strftime("%m/%d/%Y"), "Beginning", prev_month_ending_bal, prev_month_ending_bal], table_range=f'A{self.get_last_row(sheet)+1}')

        return sheet

    def do_POST(self):
        creds_dict = json.loads(os.environ.get("CREDS_JSON"))
        google = gspread.auth.service_account_from_dict(creds_dict)

        spreadsheet = google.open("Budget")

        date = datetime.now(ZoneInfo("America/New_York"))

        all_sheets = [sheet.title for sheet in spreadsheet.worksheets()]
        date_month = f'{date.month}-{date.year}'

        if date_month in all_sheets:
            sheet = spreadsheet.worksheet(date_month)
        else:
            sheet = self.create_worksheet(spreadsheet, date) 

        row = self.get_last_row(sheet)

        content_length = int(self.headers.get('Content-Length'), 0)
        body = self.rfile.read(content_length)
        data = json.loads(body)

        m_d_y = date.strftime("%m/%d/%Y")
        description = data['description']
        amount = -float(data['price'])
        if data['category'].lower() == 'income':
            amount = -amount
        total = float(sheet.acell(f'D{row}').value) + amount

        sheet.append_row([m_d_y, description, amount, total])

        self.respond()