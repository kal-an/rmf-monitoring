import io

import xlsxwriter


def create_xls(data):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('report')
    bold_format = workbook.add_format(({'bold': True}))

    col = 0
    row = 0
    for title, values in data.items():
        worksheet.write(row, col, title, bold_format)
        for time, value in values.items():
            worksheet.write(row + 1, col, time)
            worksheet.write_number(row + 1, col + 1, float(value))
            row += 1
        row = 0
        col += 2
    workbook.close()
    return output


def create_pdf(file_name, json):

    return file_name