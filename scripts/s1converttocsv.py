import openpyxl
import csv

excel_file = 'candidatos.xlsx'
csv_file   = 'candidatos.csv'

# Load the workbook and select a sheet
wb = openpyxl.load_workbook(excel_file, data_only=False)
sheet = wb.active  # or wb['SheetName']

# Prepare a CSV writer
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)

    for row in sheet.iter_rows():
        row_data = []
        for cell in row:
            # Check if there's a hyperlink
            if cell.hyperlink:
                # If there's a hyperlink, extract its address
                row_data.append(cell.hyperlink.target)
            else:
                # Otherwise, fallback to cell's value
                row_data.append(cell.value)
        writer.writerow(row_data)

print("Finished writing to", csv_file)
