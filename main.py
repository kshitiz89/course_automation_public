import subprocess
subprocess.run(["playwright", "install"], shell=True)
import os
import time
from tabulate import tabulate
from stock_data import get_ohlc_for_stock
from stock_utils import append_ohlc_to_excel
from playwright.sync_api import sync_playwright
import tkinter as tk
from tkinter import simpledialog, messagebox
import tkinter.filedialog as fd
import csv

report_matched = []
report_unmatched = []
stock_inputs = {}

def extract_float(page, selector):
    try:
        val = page.locator(selector).inner_text()
        return float(val.strip())
    except:
        return None

def open_stock_tab(context, symbol, ohlc_data, lr, ur):
    page = context.new_page()
    page.goto("https://amanchughventures.com/dnd-screen-uz/", timeout=60000)
    time.sleep(2)

    # Fill OHLC values
    if ohlc_data and len(ohlc_data) >= 2:
        day1, day2 = ohlc_data[1], ohlc_data[0]

        page.fill("#x", str(day1["High"]))
        page.fill("#y", str(day1["Low"]))
        page.fill("#z", str(day1["Close"]))

        page.fill("#h1", str(day2["High"]))
        page.fill("#l1", str(day2["Low"]))
        page.fill("#c1", str(day2["Close"]))
    else:
        print(f"⚠️ Skipping {symbol} due to missing OHLC data")
        page.close()
        return

    time.sleep(2)

    fcmz2_ls = extract_float(page, "label[name='fcmz2_ls']")
    fcmz1 = extract_float(page, "label[name='fcmz1']")
    fcmz2 = extract_float(page, "label[name='fcmz2']")
    fcnz3 = extract_float(page, "label[name='fcnz3']")
    fcnz3_us = extract_float(page, "label[name='fcnz3_us']")
    fcnz2_us = extract_float(page, "label[name='fcnz2_us']")
    fcmz1_us = extract_float(page, "label[name='fcmz1_us']")

    matched = False
    buy_1 = buy_2 = ""

    if lr >= fcmz2_ls:
        if fcmz1 <= lr <= fcmz2:
            matched = True
            buy_1 = fcnz3_us
            buy_2 = fcmz1_us
        elif fcnz3 <= lr <= fcmz1:
            matched = True
            buy_1 = fcnz2_us
            buy_2 = fcnz3_us
        elif fcmz2_ls <= lr <= fcmz2:
            matched = True
            buy_1 = fcmz1

    if matched:
        report_matched.append([symbol, buy_1, buy_2])
    else:
        report_unmatched.append([symbol])

    try:
        with page.expect_download() as download_info:
            page.click("button[onclick*='downloadExcel']")
        download = download_info.value
        file_path = f"downloads/{symbol}_daily_data.xlsx"
        download.save_as(file_path)
        print(f"✅ Downloaded for {symbol}")

        # Add OHLC to the same sheet in Excel
        append_ohlc_to_excel(file_path, symbol, ohlc_data)  # ✅ pass both days

    except Exception as e:
        print(f"⚠️ Could not download for {symbol}: {e}")

    page.close()

def get_user_input():
    root = tk.Tk()
    root.withdraw()

    use_csv = messagebox.askyesno("Input Method", "Do you want to upload a CSV file?")

    if use_csv:
        file_path = fd.askopenfilename(title="Select CSV file", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            messagebox.showerror("Error", "No file selected.")
            root.destroy()
            return

        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    symbol = row["symbol"].strip().upper()
                    lr = float(row["LR"])
                    ur = float(row["UR"])
                    stock_inputs[symbol] = {"LR": lr, "UR": ur}
        except Exception as e:
            messagebox.showerror("CSV Error", f"Failed to read CSV: {e}")
    else:
        messagebox.showinfo("Stock Input", "You will now enter stock details one by one. Click Cancel to stop.")
        while True:
            symbol = simpledialog.askstring("Stock Symbol", "Enter stock symbol (e.g., RELIANCE):")
            if not symbol:
                break
            try:
                lr = float(simpledialog.askstring("LR", f"Enter LR value for {symbol}:"))
                ur = float(simpledialog.askstring("UR", f"Enter UR value for {symbol}:"))
                stock_inputs[symbol.upper()] = {"LR": lr, "UR": ur}
            except:
                messagebox.showerror("Invalid Input", "Please enter valid numeric values for LR and UR.")

    root.destroy()

def main():
    os.makedirs("downloads", exist_ok=True)
    get_user_input()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)

        for symbol, values in stock_inputs.items():
            lr = values["LR"]
            ur = values["UR"]

            yf_symbol = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
            ohlc_data = get_ohlc_for_stock(yf_symbol)

            if ohlc_data and len(ohlc_data) >= 2:
                open_stock_tab(context, symbol, ohlc_data, lr, ur)
            else:
                print(f"⚠️ Skipping {symbol} due to insufficient OHLC data.")

        browser.close()

    matched_table = tabulate(report_matched, headers=["Stock", "Buy Value 1", "Buy Value 2"], tablefmt="grid")
    unmatched_table = tabulate(report_unmatched, headers=["Stock"], tablefmt="grid")

    full_report = f"Stocks Matching Criteria:\n{matched_table}\n\nStocks Not Matching Criteria:\n{unmatched_table}"

    with open("report.txt", "w") as f:
        f.write(full_report)

    print("\n📄 Report saved to report.txt")

if __name__ == "__main__":
    main()
