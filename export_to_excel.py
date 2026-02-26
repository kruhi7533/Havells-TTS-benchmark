import pandas as pd

# =========================
# LOAD FILES
# =========================
raw_df = pd.read_csv("logs/latency_raw.csv")
summary_df = pd.read_csv("logs/latency_summary.csv")

# Optional concurrency sheets (if they exist)
try:
    batch_df = pd.read_csv("logs/concurrency_batch_avg.csv")
except:
    batch_df = None

try:
    concurrency_summary_df = pd.read_csv("logs/concurrency_summary.csv")
except:
    concurrency_summary_df = None


# =========================
# CREATE EXCEL
# =========================
with pd.ExcelWriter("tts_benchmark_report.xlsx", engine="xlsxwriter") as writer:
    
    raw_df.to_excel(writer, sheet_name="Raw Sequential", index=False)
    summary_df.to_excel(writer, sheet_name="Sequential Summary", index=False)

    if batch_df is not None:
        batch_df.to_excel(writer, sheet_name="Batch Averages", index=False)

    if concurrency_summary_df is not None:
        concurrency_summary_df.to_excel(writer, sheet_name="Concurrency Summary", index=False)

    workbook = writer.book

    # Common formats
    header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'middle',
        'border': 1,
        'bg_color': '#D9E1F2'
    })

    center_format = workbook.add_format({
        'align': 'center'
    })

    number_format = workbook.add_format({
        'num_format': '0.00',
        'align': 'center'
    })

    wrap_format = workbook.add_format({
        'text_wrap': True
    })

    # =========================
    # FORMAT RAW SHEET
    # =========================
    raw_sheet = writer.sheets["Raw Sequential"]
    raw_sheet.freeze_panes(1, 0)

    for col_num, col_name in enumerate(raw_df.columns):
        raw_sheet.write(0, col_num, col_name, header_format)

        col_width = max(
            raw_df[col_name].astype(str).map(len).max(),
            len(col_name)
        )

        raw_sheet.set_column(col_num, col_num, min(col_width + 3, 50))

    # Make text column wider + wrapped
    if "text" in raw_df.columns:
        text_index = raw_df.columns.get_loc("text")
        raw_sheet.set_column(text_index, text_index, 50, wrap_format)

    # Convert latency_seconds to ms visually
    if "latency_seconds" in raw_df.columns:
        latency_index = raw_df.columns.get_loc("latency_seconds")
        raw_sheet.set_column(latency_index, latency_index, 15, number_format)

    # =========================
    # FORMAT SEQUENTIAL SUMMARY
    # =========================
    summary_sheet = writer.sheets["Sequential Summary"]
    summary_sheet.freeze_panes(1, 0)

    for col_num, col_name in enumerate(summary_df.columns):
        summary_sheet.write(0, col_num, col_name, header_format)

    summary_sheet.set_column(0, len(summary_df.columns)-1, 20, center_format)

    # =========================
    # FORMAT BATCH AVERAGES
    # =========================
    if batch_df is not None:
        batch_sheet = writer.sheets["Batch Averages"]
        batch_sheet.freeze_panes(1, 0)

        for col_num, col_name in enumerate(batch_df.columns):
            batch_sheet.write(0, col_num, col_name, header_format)

        batch_sheet.set_column(0, len(batch_df.columns)-1, 22, center_format)

    # =========================
    # FORMAT CONCURRENCY SUMMARY
    # =========================
    if concurrency_summary_df is not None:
        conc_sheet = writer.sheets["Concurrency Summary"]
        conc_sheet.freeze_panes(1, 0)

        for col_num, col_name in enumerate(concurrency_summary_df.columns):
            conc_sheet.write(0, col_num, col_name, header_format)

        conc_sheet.set_column(0, len(concurrency_summary_df.columns)-1, 22, center_format)

print("Professional formatted Excel report created!")