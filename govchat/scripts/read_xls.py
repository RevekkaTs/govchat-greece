import xlrd

files = {
    2021: r'C:\Users\RevekkaTsouloufi\Downloads\troxaia-atyximata-2021.xls',
    2022: r'C:\Users\RevekkaTsouloufi\Downloads\troxaia-atyximata-2022.xls',
    2023: r'C:\Users\RevekkaTsouloufi\Downloads\troxaia-atyximata-2023.xls',
    2024: r'C:\Users\RevekkaTsouloufi\Downloads\troxaia-atyximata-2024.xls',
    2025: r'C:\Users\RevekkaTsouloufi\Downloads\troxaia-atyximata-2025.xls',
}

for year, path in files.items():
    try:
        wb = xlrd.open_workbook(path)
        ws = wb.sheet_by_index(0)
        print(f'--- {year} ---')
        for i in range(ws.nrows):
            row = [str(ws.cell_value(i, j)).strip() for j in range(ws.ncols)]
            if any(r for r in row):
                print(row)
    except Exception as e:
        print(f'{year}: ERROR {e}')
