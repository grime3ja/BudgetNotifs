import gspread, os, json
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from zoneinfo import ZoneInfo

class handler(BaseHTTPRequestHandler):
    def respond(self):
        response = json.dumps({"status": "ok"})
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode())

    def do_POST(self):
        creds_dict = json.loads(os.environ.get("CREDS_JSON"))
        google = gspread.auth.service_account_from_dict(creds_dict)
        row = int(os.environ.get("EXCEL_ROW"))

        spreadsheet = google.open("Budget")

        date = datetime.now(ZoneInfo("America/New_York"))
        sheet = spreadsheet.worksheet(f'{date.month}-{date.year}')

        content_length = int(self.headers.get('Content-Length'), 0)
        body = self.rfile.read(content_length)
        data = json.loads(body)

        m_d_y = date.strftime("%m/%d/%Y")
        description = data['description']
        amount = float(data['price'])
        total = float(sheet.acell(f'D{row-1}').value) - amount

        sheet.update(f"A{row}", [[m_d_y, description, amount, total]])

        os.environ.update({"EXCEL_ROW": str(row + 1)})
        self.respond()