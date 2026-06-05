import gspread, os, json
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from zoneinfo import ZoneInfo
from gspread_formatting import *


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # get google stuff
        creds_dict = json.loads(os.environ.get("CREDS_JSON"))
        google = gspread.auth.service_account_from_dict(creds_dict)

        spreadsheet = google.open("Budget")

        date = datetime.now(ZoneInfo("America/New_York"))

        # check if you need to make a new sheet for the current month
        all_sheets = [sheet.title for sheet in spreadsheet.worksheets()]
        date_month = f'{date.month}-{date.year}'

        if date_month in all_sheets:
            sheet = spreadsheet.worksheet(date_month)
        else:
            sheet = self.create_worksheet(spreadsheet, date) 

        # assume checking, change to savings if necessary
        row = self.get_last_row(sheet, 1)

        content_length = int(self.headers.get('Content-Length'), 0)
        # read from POST request
        body = self.rfile.read(content_length)
        data = json.loads(body)

        m_d_y = date.strftime("%m/%d/%Y")
        description = data['description']
        
        # assume its an expense, make an increase if necessary
        amount = -float(data['price'])
        if data['category'].lower() in ('income', 'savings_deposit'):
            amount = -amount
        
        if 'savings' in data['category'].lower():
            total_c = float(sheet.acell(f'D{row}').value) - amount

            savings_row = self.get_last_row(sheet, 6)
            total_s = float(sheet.acell(f'I{savings_row}').value) + amount
            sheet.append_row([m_d_y, description, -amount, total_c, '', m_d_y, description, amount, total_s], table_range=f'A{max(row, savings_row) + 1}')
        else:
            total = float(sheet.acell(f'D{row}').value) + amount
            sheet.append_row([m_d_y, description, amount, total], table_range=f'A{row + 1}')

        self.respond()


    def get_last_row(self, sheet, col):
        # 1 is A, 6 is F
        return len(sheet.col_values(col))


    def prev_ending(self, spreadsheet):
        prev_sheet = spreadsheet.worksheets()[-1]
        c_row = self.get_last_row(prev_sheet, 1)
        s_row = self.get_last_row(prev_sheet, 6)

        # D*row* for checking, I*row* for savings
        return (prev_sheet.cell(c_row, 4).value, prev_sheet.cell(s_row, 9).value)


    def create_worksheet(self, spreadsheet, date: datetime):
        prev_month_ending_bal = self.prev_ending(spreadsheet)

        # create new sheet and add default start
        spreadsheet.add_worksheet(f'{date.month}-{date.year}', 1, 1)
        sheet = spreadsheet.worksheet(f'{date.month}-{date.year}')
        sheet.append_rows([["Checking", "", "", "", "", "Savings", "", "", ""],
                           ["Date", "Description", "Amount", "Total", "", "Date", "Description", "Amount", "Total"]])
        rows = (self.get_last_row(sheet, 1), self.get_last_row(sheet, 6))

        # merge and center
        sheet.merge_cells("A1:D1")
        sheet.merge_cells("F1:I1")
        format_cell_range(sheet, "A1:D1", CellFormat(horizontalAlignment="CENTER", verticalAlignment="MIDDLE"))
        format_cell_range(sheet, "F1:I1", CellFormat(horizontalAlignment="CENTER", verticalAlignment="MIDDLE"))

        # add previous month's ending balance for both checking and savings
        sheet.append_row([date.strftime("%m/%d/%Y"), "Beginning", prev_month_ending_bal[0], prev_month_ending_bal[0]], table_range=f'A{rows[0] + 1}')
        sheet.append_row([date.strftime("%m/%d/%Y"), "Beginning", prev_month_ending_bal[1], prev_month_ending_bal[1]], table_range=f'F{rows[1] + 1}')

        return sheet


    def respond(self):
        response = json.dumps({"status": "ok"})
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode())
