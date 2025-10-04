import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
import matplotlib.font_manager as fm


def set_japanese_font():
    candidates = ["Yu Gothic UI","Yu Gothic","Meiryo","IPAexGothic","Noto Sans CJK JP"]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


def draw_single_day_gantt(csv_path, output_path):
    """
    Draw a 1-day schedule Gantt chart from CSV.
    CSV columns: Task, StartDate, StartTime, EndTime, Owner, Notes
    """
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="cp932")
    df["StartDT"] = pd.to_datetime(df["StartDate"] + " " + df["StartTime"])
    df["EndDT"] = pd.to_datetime(df["StartDate"] + " " + df["EndTime"])
    df = df.sort_values("StartDT").reset_index(drop=True)
    set_japanese_font()
    fig = plt.figure(figsize=(12,5), dpi=200)
    ax = plt.gca()
    y_positions = list(range(len(df)))[::-1]
    for y, (_, r) in zip(y_positions, df.iterrows()):
        duration = (r["EndDT"] - r["StartDT"]).total_seconds() / 86400.0
        ax.barh(y, duration, left=mdates.date2num(r["StartDT"]), height=0.6)
        label = f'{r["Task"]}〔{r.get("Owner","")}〕'
        ax.text(mdates.date2num(r["EndDT"]) + 0.002, y, label, va="center", fontsize=8)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(df["Task"].iloc[::-1])
    start_view = df["StartDT"].min().replace(hour=8, minute=0)
    end_view = df["EndDT"].max().replace(hour=18, minute=0)
    ax.set_xlim(mdates.date2num(start_view), mdates.date2num(end_view))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set_xlabel("時刻")
    ax.set_title("1日集中タイムテーブル")
    ax.grid(axis="x", linestyle=":", linewidth=0.5)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def draw_multi_day_gantt(csv_path, output_path):
    """
    Draw a multi-day schedule Gantt chart from CSV.
    CSV columns: Task, Start, DurationDays, Owner, Notes
    """
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="cp932")
    df["Start"] = pd.to_datetime(df["Start"])
    df["DurationDays"] = pd.to_numeric(df["DurationDays"])
    df["End"] = df["Start"] + df["DurationDays"].apply(lambda d: timedelta(days=float(d)))
    df["Duration"] = (df["End"] - df["Start"]).dt.total_seconds()/(24*3600)
    df = df.sort_values("Start").reset_index(drop=True)
    set_japanese_font()
    fig = plt.figure(figsize=(12,5), dpi=200)
    ax = plt.gca()
    y_positions = list(range(len(df)))[::-1]
    for y, (_, r) in zip(y_positions, df.iterrows()):
        ax.barh(y, r["Duration"], left=mdates.date2num(r["Start"]), height=0.6)
        label = f'{r["Task"]}〔{r.get("Owner","")}〕'
        ax.text(mdates.date2num(r["Start"]) + r["Duration"] + 0.02, y, label, va="center", fontsize=8)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(df["Task"].iloc[::-1])
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax.set_xlabel("日付")
    ax.set_title("日単位スケジュール")
    ax.grid(axis="x", linestyle=":", linewidth=0.5)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    # Example usage:
    draw_single_day_gantt("schedule_day_example.csv", "single_day_gantt.png")
    draw_multi_day_gantt("schedule_example.csv", "multi_day_gantt.png")
