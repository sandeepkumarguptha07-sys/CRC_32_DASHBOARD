import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os
from datetime import datetime

# ============================================================
# CLASSROOM MESSAGE INTEGRITY TOOL - CRC-32
# Modern Tkinter UI | Text + Universal File Verification
# ============================================================

DEFAULT_GENERATOR = "100000100110000010001110110110111"

sender_file = ""
sender_crc = ""
results = []

# ----------------------------- COLORS -------------------------
BG = "#0b1220"
PANEL = "#111b2e"
CARD = "#17243a"
CARD_2 = "#1d2d47"
TEXT = "#eaf2ff"
MUTED = "#9fb0c8"
ACCENT = "#38bdf8"
GREEN = "#22c55e"
RED = "#ef4444"
ORANGE = "#f59e0b"
BORDER = "#263a57"


# ============================================================
# CRC FUNCTIONS
# ============================================================

def crc(data, generator):
    data = list(data)
    generator = list(generator)

    for i in range(len(data) - len(generator) + 1):
        if data[i] == "1":
            for j in range(len(generator)):
                data[i + j] = str(
                    int(data[i + j]) ^ int(generator[j])
                )

    return "".join(data[-(len(generator) - 1):])


def valid_generator(generator):
    return (
        len(generator) == 33
        and all(bit in "01" for bit in generator)
        and generator[0] == "1"
        and generator[-1] == "1"
    )


def text_to_binary(text):
    return "".join(format(ord(char), "08b") for char in text)


def file_to_binary(file_name):
    # Raw bytes allow PDF, DOCX, XLSX, PPTX, JPG, PNG, MP4, ZIP, TXT, etc.
    with open(file_name, "rb") as file:
        file_data = file.read()

    return "".join(format(byte, "08b") for byte in file_data)


def calculate_file_crc(file_name, generator):
    binary_data = file_to_binary(file_name)
    padded_data = binary_data + "0" * (len(generator) - 1)
    return crc(padded_data, generator)


# ============================================================
# HELPERS
# ============================================================

def set_status(text, kind="normal"):
    status_var.set(text)

    if kind == "valid":
        status_label.configure(foreground=GREEN)
    elif kind == "error":
        status_label.configure(foreground=RED)
    elif kind == "warning":
        status_label.configure(foreground=ORANGE)
    else:
        status_label.configure(foreground=ACCENT)


def log(message):
    output_text.configure(state="normal")
    output_text.insert("end", message + "\n")
    output_text.see("end")
    output_text.configure(state="disabled")


def clear_log():
    output_text.configure(state="normal")
    output_text.delete("1.0", "end")
    output_text.configure(state="disabled")


def browse_file(title):
    return filedialog.askopenfilename(
        title=title,
        filetypes=[("All Files", "*.*")]
    )


def show_file_info(path):
    return (
        os.path.basename(path),
        os.path.splitext(path)[1] or "No extension",
        f"{os.path.getsize(path):,} bytes"
    )


# ============================================================
# DASHBOARD
# ============================================================

def update_dashboard():
    total = len(results)
    valid = sum(r["Status"] == "VALID" for r in results)
    corrupted = sum(r["Status"] == "CORRUPTED" for r in results)
    errors = sum(r["Status"] == "ERROR" for r in results)

    total_var.set(str(total))
    valid_var.set(str(valid))
    corrupted_var.set(str(corrupted))
    error_var.set(str(errors))
    error_rate_var.set(f"{(corrupted / total) * 100:.2f}%" if total else "0.00%")


# ============================================================
# CLASSROOM MESSAGE
# ============================================================

def generate_message_crc():
    message = message_entry.get().strip()
    generator = generator_entry.get().strip()

    if not message:
        messagebox.showwarning("Missing Message", "Enter a classroom announcement.")
        return

    if not valid_generator(generator):
        messagebox.showerror(
            "Invalid Generator",
            "CRC-32 generator must be exactly 33 bits and contain only 0 and 1."
        )
        return

    data = text_to_binary(message)
    padded_data = data + "0" * 32
    remainder = crc(padded_data, generator)
    codeword = data + remainder

    message_crc_var.set(remainder)
    message_codeword_var.set(codeword)
    message_length_var.set(str(len(codeword)))

    message_binary_text.configure(state="normal")
    message_binary_text.delete("1.0", "end")
    message_binary_text.insert("1.0", data)
    message_binary_text.configure(state="disabled")

    set_status("MESSAGE CRC GENERATED", "valid")
    log("----- CLASSROOM MESSAGE -----")
    log("Message   : " + message)
    log("CRC-32    : " + remainder)
    log("Codeword  : " + codeword)
    log("")


# ============================================================
# SENDER FILE
# ============================================================

def select_sender_file():
    global sender_file, sender_crc

    generator = generator_entry.get().strip()

    if not valid_generator(generator):
        messagebox.showerror(
            "Invalid Generator",
            "CRC-32 generator must be exactly 33 bits."
        )
        return

    file_name = browse_file("Select Original Sender File")

    if not file_name:
        return

    try:
        sender_file = file_name
        sender_crc = calculate_file_crc(file_name, generator)

        name, extension, size = show_file_info(file_name)

        file_sender_var.set(name)
        file_sender_crc_var.set(sender_crc)
        file_sender_size_var.set(size)

        set_status("SENDER CRC CREATED", "valid")

        log("----- FILE SENDER -----")
        log("File       : " + file_name)
        log("File Type  : " + extension)
        log("File Size  : " + size)
        log("CRC-32     : " + sender_crc)
        log("")

    except Exception as e:
        set_status("FILE ERROR", "error")
        messagebox.showerror("File Error", str(e))


# ============================================================
# SINGLE RECEIVER FILE
# ============================================================

def verify_receiver_file():
    generator = generator_entry.get().strip()

    if not valid_generator(generator):
        messagebox.showerror(
            "Invalid Generator",
            "CRC-32 generator must be exactly 33 bits."
        )
        return

    if not sender_crc:
        messagebox.showwarning(
            "Sender File Required",
            "Select the original sender file first."
        )
        return

    file_name = browse_file("Select Received File")

    if not file_name:
        return

    try:
        receiver_crc = calculate_file_crc(file_name, generator)
        name, extension, size = show_file_info(file_name)

        file_receiver_var.set(name)
        file_receiver_crc_var.set(receiver_crc)
        file_receiver_size_var.set(size)

        if receiver_crc == sender_crc:
            result = "VALID FILE - NO ERROR DETECTED"
            set_status(result, "valid")
            result_badge.configure(text="✓  VALID", foreground=GREEN)
        else:
            result = "CORRUPTED FILE - ERROR DETECTED"
            set_status(result, "error")
            result_badge.configure(text="✕  CORRUPTED", foreground=RED)

        log("----- FILE RECEIVER -----")
        log("File        : " + file_name)
        log("File Size   : " + size)
        log("Sender CRC  : " + sender_crc)
        log("Receiver CRC: " + receiver_crc)
        log("Result      : " + result)
        log("")

        messagebox.showinfo(
            "CRC-32 File Verification",
            result +
            "\n\nSender CRC-32:\n" + sender_crc +
            "\n\nReceived CRC-32:\n" + receiver_crc
        )

    except Exception as e:
        set_status("FILE ERROR", "error")
        messagebox.showerror("File Error", str(e))


# ============================================================
# BATCH VERIFICATION
# ============================================================

def batch_verify_files():
    generator = generator_entry.get().strip()

    if not valid_generator(generator):
        messagebox.showerror(
            "Invalid Generator",
            "CRC-32 generator must be exactly 33 bits."
        )
        return

    if not sender_crc:
        messagebox.showwarning(
            "Sender File Required",
            "Select the original sender file first."
        )
        return

    files = filedialog.askopenfilenames(
        title="Select Received Files",
        filetypes=[("All Files", "*.*")]
    )

    if not files:
        return

    for item in result_tree.get_children():
        result_tree.delete(item)

    results.clear()

    for file_name in files:
        try:
            receiver_crc = calculate_file_crc(file_name, generator)
            status = "VALID" if receiver_crc == sender_crc else "CORRUPTED"

            record = {
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "File Name": os.path.basename(file_name),
                "File Type": os.path.splitext(file_name)[1] or "No extension",
                "File Size": os.path.getsize(file_name),
                "Sender CRC": sender_crc,
                "Received CRC": receiver_crc,
                "Status": status
            }

            results.append(record)

            tag = "valid" if status == "VALID" else "corrupted"
            result_tree.insert(
                "",
                "end",
                values=(
                    record["File Name"],
                    record["File Type"],
                    f"{record['File Size']:,}",
                    record["Received CRC"],
                    record["Status"]
                ),
                tags=(tag,)
            )

        except Exception as e:
            record = {
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "File Name": os.path.basename(file_name),
                "File Type": os.path.splitext(file_name)[1] or "No extension",
                "File Size": "-",
                "Sender CRC": sender_crc,
                "Received CRC": str(e),
                "Status": "ERROR"
            }

            results.append(record)

            result_tree.insert(
                "",
                "end",
                values=(
                    record["File Name"],
                    record["File Type"],
                    "-",
                    record["Received CRC"],
                    "ERROR"
                ),
                tags=("error",)
            )

    update_dashboard()

    total = len(results)
    valid = sum(r["Status"] == "VALID" for r in results)
    corrupted = sum(r["Status"] == "CORRUPTED" for r in results)
    errors = sum(r["Status"] == "ERROR" for r in results)

    if corrupted:
        set_status(f"BATCH COMPLETE • {corrupted} CORRUPTED", "error")
    elif errors:
        set_status(f"BATCH COMPLETE • {errors} ERROR(S)", "warning")
    else:
        set_status("BATCH COMPLETE • ALL FILES VALID", "valid")

    log("----- BATCH FILE VERIFICATION -----")
    log("Original File : " + os.path.basename(sender_file))
    log("Sender CRC-32 : " + sender_crc)
    log("Total Checked : " + str(total))
    log("Valid         : " + str(valid))
    log("Corrupted     : " + str(corrupted))
    log("Errors        : " + str(errors))
    log("")


# ============================================================
# CSV REPORT
# ============================================================

def generate_csv_report():
    if not results:
        messagebox.showwarning(
            "No Results",
            "Run batch verification first."
        )
        return

    file_name = filedialog.asksaveasfilename(
        title="Save CRC Verification Report",
        initialfile="CRC_Verification_Report.csv",
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )

    if not file_name:
        return

    try:
        with open(file_name, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "Time",
                    "File Name",
                    "File Type",
                    "File Size",
                    "Sender CRC",
                    "Received CRC",
                    "Status"
                ]
            )
            writer.writeheader()
            writer.writerows(results)

        set_status("CSV REPORT GENERATED", "valid")
        log("CSV Report saved: " + file_name)
        messagebox.showinfo(
            "Report Generated",
            "CSV report saved successfully:\n" + file_name
        )

    except Exception as e:
        messagebox.showerror("Report Error", str(e))


# ============================================================
# RESET
# ============================================================

def reset_all():
    global sender_file, sender_crc

    sender_file = ""
    sender_crc = ""
    results.clear()

    message_entry.delete(0, "end")
    message_entry.insert(0, "Exam will be conducted on Monday")

    generator_entry.delete(0, "end")
    generator_entry.insert(0, DEFAULT_GENERATOR)

    file_sender_var.set("No sender file selected")
    file_sender_crc_var.set("-")
    file_sender_size_var.set("-")

    file_receiver_var.set("No receiver file selected")
    file_receiver_crc_var.set("-")
    file_receiver_size_var.set("-")

    message_crc_var.set("-")
    message_codeword_var.set("-")
    message_length_var.set("-")

    message_binary_text.configure(state="normal")
    message_binary_text.delete("1.0", "end")
    message_binary_text.configure(state="disabled")

    result_badge.configure(text="WAITING", foreground=MUTED)
    set_status("READY FOR VERIFICATION", "normal")

    for item in result_tree.get_children():
        result_tree.delete(item)

    total_var.set("0")
    valid_var.set("0")
    corrupted_var.set("0")
    error_var.set("0")
    error_rate_var.set("0.00%")

    clear_log()


# ============================================================
# UI HELPERS
# ============================================================

def make_card(parent, title, subtitle=None):
    outer = tk.Frame(
        parent,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    outer.pack(fill="x", pady=8)

    header = tk.Frame(outer, bg=PANEL)
    header.pack(fill="x", padx=16, pady=(12, 4))

    tk.Label(
        header,
        text=title,
        bg=PANEL,
        fg=TEXT,
        font=("Segoe UI", 12, "bold")
    ).pack(side="left")

    if subtitle:
        tk.Label(
            header,
            text=subtitle,
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(side="right")

    body = tk.Frame(outer, bg=PANEL)
    body.pack(fill="x", padx=16, pady=(4, 14))
    return body


def styled_button(parent, text, command, primary=False):
    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=ACCENT if primary else CARD_2,
        fg="#06111f" if primary else TEXT,
        activebackground=ACCENT,
        activeforeground="#06111f",
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 10, "bold"),
        padx=16,
        pady=9
    )
    return button


def dashboard_card(parent, title, variable):
    frame = tk.Frame(
        parent,
        bg=CARD,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    frame.pack(side="left", fill="both", expand=True, padx=5)

    tk.Label(
        frame,
        text=title,
        bg=CARD,
        fg=MUTED,
        font=("Segoe UI", 9, "bold")
    ).pack(pady=(10, 2))

    tk.Label(
        frame,
        textvariable=variable,
        bg=CARD,
        fg=TEXT,
        font=("Segoe UI", 20, "bold")
    ).pack(pady=(0, 10))


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()
root.title("Classroom Message Integrity Tool • CRC-32")
root.geometry("1380x950")
root.minsize(1100, 760)
root.configure(bg=BG)

# ----------------------------- VARIABLES ----------------------
file_sender_var = tk.StringVar(value="No sender file selected")
file_sender_crc_var = tk.StringVar(value="-")
file_sender_size_var = tk.StringVar(value="-")

file_receiver_var = tk.StringVar(value="No receiver file selected")
file_receiver_crc_var = tk.StringVar(value="-")
file_receiver_size_var = tk.StringVar(value="-")

message_crc_var = tk.StringVar(value="-")
message_codeword_var = tk.StringVar(value="-")
message_length_var = tk.StringVar(value="-")

total_var = tk.StringVar(value="0")
valid_var = tk.StringVar(value="0")
corrupted_var = tk.StringVar(value="0")
error_var = tk.StringVar(value="0")
error_rate_var = tk.StringVar(value="0.00%")
status_var = tk.StringVar(value="READY FOR VERIFICATION")

# ----------------------------- STYLE ---------------------------
style = ttk.Style()
try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure(
    "Treeview",
    background=CARD,
    fieldbackground=CARD,
    foreground=TEXT,
    rowheight=32,
    borderwidth=0,
    font=("Segoe UI", 9)
)
style.configure(
    "Treeview.Heading",
    background=CARD_2,
    foreground=TEXT,
    relief="flat",
    font=("Segoe UI", 9, "bold")
)
style.map(
    "Treeview",
    background=[("selected", "#29415f")],
    foreground=[("selected", TEXT)]
)
style.configure(
    "Vertical.TScrollbar",
    background=CARD_2,
    troughcolor=PANEL,
    bordercolor=PANEL,
    arrowcolor=MUTED
)

# ----------------------------- HEADER --------------------------
header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=28, pady=(22, 8))

title_box = tk.Frame(header, bg=BG)
title_box.pack(side="left")

tk.Label(
    title_box,
    text="CRC-32",
    bg=BG,
    fg=ACCENT,
    font=("Segoe UI", 25, "bold")
).pack(anchor="w")

tk.Label(
    title_box,
    text="CLASSROOM MESSAGE INTEGRITY TOOL",
    bg=BG,
    fg=TEXT,
    font=("Segoe UI", 18, "bold")
).pack(anchor="w")

tk.Label(
    title_box,
    text="Detect transmission errors in classroom messages and any file type",
    bg=BG,
    fg=MUTED,
    font=("Segoe UI", 10)
).pack(anchor="w", pady=(2, 0))

status_box = tk.Frame(
    header,
    bg=PANEL,
    highlightbackground=BORDER,
    highlightthickness=1,
    padx=16,
    pady=10
)
status_box.pack(side="right", anchor="n")

tk.Label(
    status_box,
    text="SYSTEM STATUS",
    bg=PANEL,
    fg=MUTED,
    font=("Segoe UI", 8, "bold")
).pack()

status_label = tk.Label(
    status_box,
    textvariable=status_var,
    bg=PANEL,
    fg=ACCENT,
    font=("Segoe UI", 10, "bold")
)
status_label.pack()

# ----------------------------- SCROLLABLE CONTENT -------------
canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
scrollbar_main = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
content = tk.Frame(canvas, bg=BG)

content.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas_window = canvas.create_window(
    (0, 0),
    window=content,
    anchor="nw"
)

def resize_content(event):
    canvas.itemconfigure(canvas_window, width=event.width)

canvas.bind("<Configure>", resize_content)
canvas.configure(yscrollcommand=scrollbar_main.set)

canvas.pack(side="left", fill="both", expand=True, padx=(24, 0))
scrollbar_main.pack(side="right", fill="y", padx=(0, 18), pady=5)

def mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", mousewheel)

# ----------------------------- MESSAGE CARD -------------------
message_body = make_card(
    content,
    "01  •  CLASSROOM MESSAGE",
    "Faculty announcement → binary → CRC-32 codeword"
)

message_body.columnconfigure(1, weight=1)

tk.Label(
    message_body,
    text="Announcement",
    bg=PANEL,
    fg=MUTED,
    font=("Segoe UI", 9, "bold")
).grid(row=0, column=0, sticky="w", padx=(0, 12), pady=6)

message_entry = tk.Entry(
    message_body,
    bg=CARD,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    font=("Segoe UI", 10)
)
message_entry.grid(row=0, column=1, sticky="ew", pady=6, ipady=8)
message_entry.insert(0, "Exam will be conducted on Monday")

tk.Label(
    message_body,
    text="33-bit Generator",
    bg=PANEL,
    fg=MUTED,
    font=("Segoe UI", 9, "bold")
).grid(row=1, column=0, sticky="w", padx=(0, 12), pady=6)

generator_entry = tk.Entry(
    message_body,
    bg=CARD,
    fg=ACCENT,
    insertbackground=TEXT,
    relief="flat",
    font=("Consolas", 10)
)
generator_entry.grid(row=1, column=1, sticky="ew", pady=6, ipady=8)
generator_entry.insert(0, DEFAULT_GENERATOR)

message_button = styled_button(
    message_body,
    "CALCULATE CRC-32",
    generate_message_crc,
    primary=True
)
message_button.grid(row=0, column=2, rowspan=2, padx=(14, 0))

# Result strip
message_result = tk.Frame(message_body, bg=CARD)
message_result.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(12, 4))
message_result.columnconfigure(1, weight=1)

tk.Label(
    message_result,
    text="CRC-32",
    bg=CARD,
    fg=MUTED,
    font=("Segoe UI", 9, "bold")
).grid(row=0, column=0, padx=12, pady=10)

tk.Label(
    message_result,
    textvariable=message_crc_var,
    bg=CARD,
    fg=GREEN,
    font=("Consolas", 11, "bold")
).grid(row=0, column=1, sticky="w")

tk.Label(
    message_result,
    text="Codeword Length",
    bg=CARD,
    fg=MUTED,
    font=("Segoe UI", 9, "bold")
).grid(row=0, column=2, padx=(20, 8))

tk.Label(
    message_result,
    textvariable=message_length_var,
    bg=CARD,
    fg=TEXT,
    font=("Segoe UI", 10, "bold")
).grid(row=0, column=3, padx=(0, 12))

tk.Label(
    message_body,
    text="Binary Data",
    bg=PANEL,
    fg=MUTED,
    font=("Segoe UI", 9, "bold")
).grid(row=3, column=0, sticky="nw", pady=(10, 4))

message_binary_text = tk.Text(
    message_body,
    height=3,
    bg="#0a1424",
    fg="#8bd8ff",
    insertbackground=TEXT,
    relief="flat",
    wrap="none",
    font=("Consolas", 8)
)
message_binary_text.grid(row=3, column=1, columnspan=2, sticky="ew", pady=(10, 4))
message_binary_text.configure(state="disabled")

# ----------------------------- FILE CARD ----------------------
file_body = make_card(
    content,
    "02  •  UNIVERSAL FILE INTEGRITY",
    "Raw-byte CRC verification • all file types supported"
)
file_body.columnconfigure(1, weight=1)

# Sender
tk.Label(
    file_body,
    text="ORIGINAL SENDER",
    bg=PANEL,
    fg=ACCENT,
    font=("Segoe UI", 9, "bold")
).grid(row=0, column=0, sticky="w", pady=6)

tk.Label(
    file_body,
    textvariable=file_sender_var,
    bg=PANEL,
    fg=TEXT,
    font=("Segoe UI", 10, "bold")
).grid(row=0, column=1, sticky="w", padx=10)

styled_button(
    file_body,
    "SELECT SENDER FILE",
    select_sender_file,
    primary=True
).grid(row=0, column=2, padx=5)

tk.Label(
    file_body,
    text="Sender CRC",
    bg=PANEL,
    fg=MUTED,
    font=("Segoe UI", 9)
).grid(row=1, column=0, sticky="w")

tk.Label(
    file_body,
    textvariable=file_sender_crc_var,
    bg=PANEL,
    fg=GREEN,
    font=("Consolas", 9, "bold")
).grid(row=1, column=1, sticky="w", padx=10)

tk.Label(
    file_body,
    textvariable=file_sender_size_var,
    bg=PANEL,
    fg=MUTED,
    font=("Segoe UI", 9)
).grid(row=1, column=2, sticky="e", padx=5)

# Receiver
tk.Frame(file_body, bg=BORDER, height=1).grid(
    row=2, column=0, columnspan=3, sticky="ew", pady=12
)

tk.Label(
    file_body,
    text="RECEIVED FILE",
    bg=PANEL,
    fg=ACCENT,
    font=("Segoe UI", 9, "bold")
).grid(row=3, column=0, sticky="w", pady=6)

tk.Label(
    file_body,
    textvariable=file_receiver_var,
    bg=PANEL,
    fg=TEXT,
    font=("Segoe UI", 10, "bold")
).grid(row=3, column=1, sticky="w", padx=10)

styled_button(
    file_body,
    "VERIFY ONE FILE",
    verify_receiver_file
).grid(row=3, column=2, padx=5)

tk.Label(
    file_body,
    text="Received CRC",
    bg=PANEL,
    fg=MUTED,
    font=("Segoe UI", 9)
).grid(row=4, column=0, sticky="w")

tk.Label(
    file_body,
    textvariable=file_receiver_crc_var,
    bg=PANEL,
    fg=TEXT,
    font=("Consolas", 9, "bold")
).grid(row=4, column=1, sticky="w", padx=10)

tk.Label(
    file_body,
    textvariable=file_receiver_size_var,
    bg=PANEL,
    fg=MUTED,
    font=("Segoe UI", 9)
).grid(row=4, column=2, sticky="e", padx=5)

# Verification status
result_status_frame = tk.Frame(file_body, bg=CARD)
result_status_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(14, 4))

result_badge = tk.Label(
    result_status_frame,
    text="WAITING",
    bg=CARD,
    fg=MUTED,
    font=("Segoe UI", 13, "bold"),
    padx=14,
    pady=10
)
result_badge.pack(side="left")

tk.Label(
    result_status_frame,
    text="Use batch verification to compare multiple received files against the same sender CRC.",
    bg=CARD,
    fg=MUTED,
    font=("Segoe UI", 9)
).pack(side="left", padx=12)

batch_button = styled_button(
    file_body,
    "BATCH VERIFY FILES",
    batch_verify_files,
    primary=True
)
batch_button.grid(row=6, column=2, padx=5, pady=(10, 2))

tk.Label(
    file_body,
    text="Supported: PDF • DOC/DOCX • XLS/XLSX • PPT/PPTX • JPG • PNG • MP4 • ZIP • TXT • ANY FILE",
    bg=PANEL,
    fg=MUTED,
    font=("Segoe UI", 8)
).grid(row=6, column=0, columnspan=2, sticky="w", pady=(10, 2))

# ----------------------------- DASHBOARD ----------------------
dash_body = make_card(
    content,
    "03  •  VERIFICATION DASHBOARD",
    "Live batch statistics"
)

cards_row = tk.Frame(dash_body, bg=PANEL)
cards_row.pack(fill="x")

dashboard_card(cards_row, "TOTAL FILES", total_var)
dashboard_card(cards_row, "VALID", valid_var)
dashboard_card(cards_row, "CORRUPTED", corrupted_var)
dashboard_card(cards_row, "ERROR", error_var)
dashboard_card(cards_row, "ERROR RATE", error_rate_var)

# ----------------------------- ACTIONS ------------------------
actions = tk.Frame(content, bg=BG)
actions.pack(fill="x", pady=6)

styled_button(
    actions,
    "GENERATE CSV REPORT",
    generate_csv_report,
    primary=True
).pack(side="left", padx=(0, 8))

styled_button(
    actions,
    "RESET",
    reset_all
).pack(side="left")

# ----------------------------- REPORT TABLE -------------------
table_body = make_card(
    content,
    "04  •  BATCH VERIFICATION REPORT",
    "CRC comparison results"
)

table_container = tk.Frame(table_body, bg=PANEL)
table_container.pack(fill="both", expand=True)

columns = (
    "File Name",
    "File Type",
    "File Size",
    "Received CRC",
    "Status"
)

result_tree = ttk.Treeview(
    table_container,
    columns=columns,
    show="headings",
    height=8
)

for column in columns:
    result_tree.heading(column, text=column)

result_tree.column("File Name", width=300, anchor="w")
result_tree.column("File Type", width=110, anchor="center")
result_tree.column("File Size", width=120, anchor="e")
result_tree.column("Received CRC", width=520, anchor="w")
result_tree.column("Status", width=130, anchor="center")

result_tree.tag_configure("valid", foreground=GREEN)
result_tree.tag_configure("corrupted", foreground=RED)
result_tree.tag_configure("error", foreground=ORANGE)

table_scroll = ttk.Scrollbar(
    table_container,
    orient="vertical",
    command=result_tree.yview
)
result_tree.configure(yscrollcommand=table_scroll.set)

result_tree.pack(side="left", fill="both", expand=True)
table_scroll.pack(side="right", fill="y")

# ----------------------------- LOG -----------------------------
log_body = make_card(
    content,
    "05  •  ACTIVITY LOG",
    "Operations and verification events"
)

output_text = tk.Text(
    log_body,
    height=7,
    bg="#08111f",
    fg="#9cc7e8",
    insertbackground=TEXT,
    relief="flat",
    font=("Consolas", 9),
    wrap="word"
)
output_text.pack(fill="x")
output_text.configure(state="disabled")

# ----------------------------- FOOTER --------------------------
footer = tk.Frame(content, bg=BG)
footer.pack(fill="x", pady=(5, 20))

tk.Label(
    footer,
    text="FACULTY  →  TRANSMISSION / NOISE  →  STUDENT  →  CRC-32 VERIFICATION  →  DASHBOARD  →  CSV REPORT",
    bg=BG,
    fg=MUTED,
    font=("Segoe UI", 8, "bold")
).pack()

# Initial log
log("CRC-32 Classroom Message Integrity Tool started.")
log("Ready. Select a sender file or enter a classroom announcement.")
log("")

root.mainloop()
