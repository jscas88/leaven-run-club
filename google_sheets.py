import os
import json
import gspread
from google.oauth2.service_account import Credentials

# Your Google Sheet ID
SHEET_ID = "11t9eYNmZ1mQRudTtVvrSaubzhzbH2adyLzVmbgAsELY"

def _get_client():
    """
    Internal helper: returns an authorized gspread client using the
    GOOGLE_CREDS_JSON environment variable.
    """
    creds_dict = json.loads(os.environ["GOOGLE_CREDS_JSON"])

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    return gspread.authorize(creds)


def get_sheet(worksheet_name):
    """
    Opens a specific worksheet/tab inside your Google Sheet.
    Example: get_sheet("Runners"), get_sheet("Attendance")
    """
    client = _get_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    return spreadsheet.worksheet(worksheet_name)


# Optional helpers you will use in app.py
def get_all_rows(worksheet_name):
    """
    Returns all rows from a worksheet as a list of lists.
    """
    sheet = get_sheet(worksheet_name)
    return sheet.get_all_values()


def append_row(worksheet_name, row_data):
    """
    Appends a row to a worksheet.
    Example: append_row("Attendance", ["Juan", "2026-08-21", "Yes"])
    """
    sheet = get_sheet(worksheet_name)
    sheet.append_row(row_data)


def update_cell(worksheet_name, row, col, value):
    """
    Updates a single cell in a worksheet.
    """
    sheet = get_sheet(worksheet_name)
    sheet.update_cell(row, col, value)
