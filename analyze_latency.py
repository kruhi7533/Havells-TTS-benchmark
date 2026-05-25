from collections import defaultdict

import pandas as pd


LOG_PATH = "logs/english_latency_raw.csv"
EXCEL_PATH = "logs/english_latency_summary.xlsx"


def main() -> None:
    # Read raw CSV
    df = pd.read_csv(LOG_PATH)

    # Filter successful rows
    df_success = df[df["status"] == "Success"].copy()

    # Normalise TTFA column name (it is already ttfa(ms) in your file)
    if "ttfa(ms)" in df_success.columns:
        ttfa_col = "ttfa(ms)"
    elif "ttfa_seconds" in df_success.columns:
        ttfa_col = "ttfa_seconds"
    else:
        raise ValueError("No TTFA column found in CSV.")

    # Ensure TTFA is numeric
    df_success[ttfa_col] = pd.to_numeric(df_success[ttfa_col], errors="coerce")
    df_success = df_success.dropna(subset=[ttfa_col])

    # Average TTFA per model
    avg_ttfa = (
        df_success.groupby("model")[ttfa_col]
        .agg(["count", "mean"])
        .rename(columns={"count": "samples", "mean": "avg_ttfa_ms"})
    )

    # Per‑sentence winner (lower TTFA)
    winners = (
        df_success.sort_values(ttfa_col)
        .groupby("text")
        .first()[["model", ttfa_col]]
        .rename(columns={"model": "winner_model", ttfa_col: "winner_ttfa_ms"})
    )

    winner_counts = (
        winners["winner_model"]
        .value_counts()
        .rename("sentences_faster")
        .to_frame()
    )

    # Overall winner by average TTFA
    if not avg_ttfa.empty:
        overall_winner = avg_ttfa["avg_ttfa_ms"].idxmin()
    else:
        overall_winner = "N/A"

    overall_df = pd.DataFrame(
        {"overall_winner": [overall_winner]}
    )

    # Write Excel with 2 sheets
    with pd.ExcelWriter(EXCEL_PATH, engine="xlsxwriter") as writer:
        # Sheet 1: raw data
        df.to_excel(writer, sheet_name="raw_data", index=False)

        # Sheet 2: conclusion/summary
        start_row = 0
        overall_df.to_excel(writer, sheet_name="conclusion", index=False, startrow=start_row)
        start_row += len(overall_df) + 2

        avg_ttfa.reset_index().to_excel(
            writer, sheet_name="conclusion", index=False, startrow=start_row
        )
        start_row += len(avg_ttfa) + 2

        winner_counts.reset_index().rename(
            columns={"index": "model"}
        ).to_excel(
            writer, sheet_name="conclusion", index=False, startrow=start_row
        )

        # Make columns wide enough so they don't visually collapse
        workbook = writer.book
        worksheet = writer.sheets["conclusion"]
        # Set first 6 columns to a comfortable width
        worksheet.set_column(0, 5, 24)


if __name__ == "__main__":
    main()

