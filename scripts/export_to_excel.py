import pandas as pd
import detailed_analyzer
import os

# =========================
# RUN DETAILED ANALYZER FOR ENGLISH
# =========================
detailed_analyzer.RAW_LOG_PATH = "../logs/english_latency_raw.csv"
detailed_analyzer.OUTPUT_EXCEL = "../outputs/detailed_english.xlsx"
detailed_analyzer.analyze()

# =========================
# RUN DETAILED ANALYZER FOR MULTILINGUAL
# =========================
detailed_analyzer.RAW_LOG_PATH = "../logs/latency_raw_multilingual.csv"
detailed_analyzer.OUTPUT_EXCEL = "../outputs/detailed_multilingual.xlsx"
detailed_analyzer.analyze()


# =========================
# LOAD FILES
# =========================
english_df = pd.read_csv("../logs/english_latency_raw.csv")
multilingual_df = pd.read_csv("../logs/latency_raw_multilingual.csv")

english_detailed_df = pd.read_excel(
    "../outputs/detailed_english.xlsx",
    sheet_name="Full Analysis"
)

multilingual_detailed_df = pd.read_excel(
    "../outputs/detailed_multilingual.xlsx",
    sheet_name="Full Analysis"
)

# Optional concurrency sheets
try:
    batch_df = pd.read_csv("../logs/concurrency_batch_avg.csv")
except:
    batch_df = None

try:
    concurrency_summary_df = pd.read_csv("../logs/concurrency_summary.csv")
except:
    concurrency_summary_df = None


# =========================
# CREATE FINAL EXCEL
# =========================
with pd.ExcelWriter("tts_benchmark_report.xlsx", engine="xlsxwriter") as writer:

    # ✅ Detailed Sheets
    english_detailed_df.to_excel(writer, sheet_name="English Detailed", index=False)
    multilingual_detailed_df.to_excel(writer, sheet_name="Multilingual Detailed", index=False)

    # ✅ Raw Sheets
    english_df.to_excel(writer, sheet_name="English Raw", index=False)
    multilingual_df.to_excel(writer, sheet_name="Multilingual Raw", index=False)

    if batch_df is not None:
        batch_df.to_excel(writer, sheet_name="Batch Averages", index=False)

    if concurrency_summary_df is not None:
        concurrency_summary_df.to_excel(writer, sheet_name="Concurrency Summary", index=False)

    workbook = writer.book

    header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'middle',
        'border': 1,
        'bg_color': '#D9E1F2'
    })

    wrap_format = workbook.add_format({'text_wrap': True})
    center_format = workbook.add_format({'align': 'center'})

    # =========================
    # FORMAT ENGLISH DETAILED
    # =========================
    eng_detail_sheet = writer.sheets["English Detailed"]
    eng_detail_sheet.freeze_panes(1, 0)

    for col_num, col_name in enumerate(english_detailed_df.columns):
        eng_detail_sheet.write(0, col_num, col_name, header_format)
        eng_detail_sheet.set_column(col_num, col_num, 20)

    # =========================
    # FORMAT MULTILINGUAL DETAILED
    # =========================
    multi_detail_sheet = writer.sheets["Multilingual Detailed"]
    multi_detail_sheet.freeze_panes(1, 0)

    for col_num, col_name in enumerate(multilingual_detailed_df.columns):
        multi_detail_sheet.write(0, col_num, col_name, header_format)
        multi_detail_sheet.set_column(col_num, col_num, 20)

    # =========================
    # FORMAT ENGLISH RAW
    # =========================
    english_sheet = writer.sheets["English Raw"]
    english_sheet.freeze_panes(1, 0)

    for col_num, col_name in enumerate(english_df.columns):
        english_sheet.write(0, col_num, col_name, header_format)
        col_width = max(
            english_df[col_name].astype(str).map(len).max(),
            len(col_name)
        )
        english_sheet.set_column(col_num, col_num, min(col_width + 3, 50))

    if "text" in english_df.columns:
        text_index = english_df.columns.get_loc("text")
        english_sheet.set_column(text_index, text_index, 50, wrap_format)

    # =========================
    # FORMAT MULTILINGUAL RAW
    # =========================
    multi_sheet = writer.sheets["Multilingual Raw"]
    multi_sheet.freeze_panes(1, 0)

    for col_num, col_name in enumerate(multilingual_df.columns):
        multi_sheet.write(0, col_num, col_name, header_format)
        col_width = max(
            multilingual_df[col_name].astype(str).map(len).max(),
            len(col_name)
        )
        multi_sheet.set_column(col_num, col_num, min(col_width + 3, 50))

    if "text" in multilingual_df.columns:
        text_index = multilingual_df.columns.get_loc("text")
        multi_sheet.set_column(text_index, text_index, 50, wrap_format)

    # =========================
    # FORMAT BATCH
    # =========================
    if batch_df is not None:
        batch_sheet = writer.sheets["Batch Averages"]
        batch_sheet.freeze_panes(1, 0)

        for col_num, col_name in enumerate(batch_df.columns):
            batch_sheet.write(0, col_num, col_name, header_format)

        batch_sheet.set_column(0, len(batch_df.columns)-1, 22, center_format)

    # =========================
    # FORMAT CONCURRENCY
    # =========================
    if concurrency_summary_df is not None:
        conc_sheet = writer.sheets["Concurrency Summary"]
        conc_sheet.freeze_panes(1, 0)

        for col_num, col_name in enumerate(concurrency_summary_df.columns):
            conc_sheet.write(0, col_num, col_name, header_format)

        conc_sheet.set_column(0, len(concurrency_summary_df.columns)-1, 22, center_format)

print("Final professional benchmark report created!")