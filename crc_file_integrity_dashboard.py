import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os
from datetime import datetime


# ============================================================
# CRC-32 CLASSROOM MESSAGE / FILE INTEGRITY TOOL
# ============================================================

# 33-bit CRC-32 generator (32-bit CRC remainder)
DEFAULT_GENERATOR = "100000100110000010001110110110111"

sender_file = ""
sender_crc = ""
results = []


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
    """
    IMPORTANT:
    Reads the file as RAW BYTES.
    Therefore PDF, DOC/DOCX, XLS/XLSX, PPT/PPTX,
    JPG, PNG, MP4, ZIP, TXT, EXE, etc. are all accepted.
    """
    with open(file_name, "rb") as file:
        file_data = file.read()

    return "".join(format(byte, "08b") for byte in file_data)


def calculate_file_crc(file_name, generator):
    binary_data = file_to_binary(file_name)

    padded_data = binary_data + "0" * (len(generator) - 1)

    return crc(padded_data, generator)


# ============================================================
# LOG
# ============================================================

def log(message):
    output_text.config(state="normal")
    output_text.insert("end", message + "\n")
    output_text.see("end")
    output_text.config(state="disabled")


def clear_log():
    output_text.config(state="normal")
    output_text.delete("1.0", "end")
    output_text.config(state="disabled")


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

    if total:
        error_rate_var.set(f"{(corrupted / total) * 100:.2f}%")
    else:
        error_rate_var.set("0.00%")


# ============================================================
# UNIVERSAL FILE - SENDER
# ============================================================

def select_sender_file():
    global sender_file, sender_crc

    generator = generator_entry.get().strip()

    if not valid_generator(generator):
        messagebox.showerror(
            "Invalid Generator",
            "CRC-32 generator must be exactly 33 bits.\n"
            "Use only 0 and 1."
        )
        return

    # NO *.txt FILTER HERE.
    # *.* means every file type is shown.
    file_name = filedialog.askopenfilename(
        title="Select ANY Sender File",
        filetypes=[("All Files", "*.*")]
    )

    if not file_name:
        return

    try:
        sender_file = file_name
        sender_crc = calculate_file_crc(file_name, generator)

        file_sender_var.set(os.path.basename(file_name))
        file_sender_crc_var.set(sender_crc)
        file_sender_size_var.set(
            f"{os.path.getsize(file_name):,} bytes"
        )

        file_result_var.set("SENDER FILE CRC CREATED")

        log("----- FILE SENDER -----")
        log("File       : " + file_name)
        log("File Type  : " + (os.path.splitext(file_name)[1] or "No extension"))
        log("File Size  : " + f"{os.path.getsize(file_name):,} bytes")
        log("CRC-32     : " + sender_crc)
        log("")

    except Exception as e:
        messagebox.showerror("File Error", str(e))


# ============================================================
# UNIVERSAL FILE - RECEIVER
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

    # NO *.txt FILTER HERE.
    file_name = filedialog.askopenfilename(
        title="Select ANY Received File",
        filetypes=[("All Files", "*.*")]
    )

    if not file_name:
        return

    try:
        receiver_crc = calculate_file_crc(file_name, generator)

        file_receiver_var.set(os.path.basename(file_name))
        file_receiver_crc_var.set(receiver_crc)
        file_receiver_size_var.set(
            f"{os.path.getsize(file_name):,} bytes"
        )

        if receiver_crc == sender_crc:
            file_result_var.set("VALID FILE - NO ERROR DETECTED")
        else:
            file_result_var.set("CORRUPTED FILE - ERROR DETECTED")

        log("----- FILE RECEIVER -----")
        log("File        : " + file_name)
        log("File Size   : " + f"{os.path.getsize(file_name):,} bytes")
        log("Sender CRC  : " + sender_crc)
        log("Receiver CRC: " + receiver_crc)
        log("Result      : " + file_result_var.get())
        log("")

        messagebox.showinfo(
            "CRC-32 File Verification",
            file_result_var.get() +
            "\n\nSender CRC-32:\n" + sender_crc +
            "\n\nReceived CRC-32:\n" + receiver_crc
        )

    except Exception as e:
        messagebox.showerror("File Error", str(e))


# ============================================================
# BATCH VERIFICATION - ALL FILE TYPES
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

    # NO *.txt FILTER HERE.
    files = filedialog.askopenfilenames(
        title="Select ANY Received Files",
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

            if receiver_crc == sender_crc:
                status = "VALID"
            else:
                status = "CORRUPTED"

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

            result_tree.insert(
                "",
                "end",
                values=(
                    record["File Name"],
                    record["File Type"],
                    f"{record['File Size']:,}",
                    record["Received CRC"],
                    record["Status"]
                )
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
                )
            )

    update_dashboard()

    log("----- BATCH FILE VERIFICATION -----")
    log("Original File : " + os.path.basename(sender_file))
    log("Sender CRC-32 : " + sender_crc)
    log("Total Checked : " + str(len(results)))
    log("Valid         : " + str(sum(r["Status"] == "VALID" for r in results)))
    log("Corrupted     : " + str(sum(r["Status"] == "CORRUPTED" for r in results)))
    log("Errors        : " + str(sum(r["Status"] == "ERROR" for r in results)))
    log("")


# ============================================================
# TEXT MESSAGE CRC
# ============================================================

def generate_message_crc():
    message = message_entry.get()
    generator = generator_entry.get().strip()

    if not message:
        messagebox.showwarning(
            "Missing Message",
            "Enter a classroom announcement."
        )
        return

    if not valid_generator(generator):
        messagebox.showerror(
            "Invalid Generator",
            "CRC-32 generator must be exactly 33 bits."
        )
        return

    data = text_to_binary(message)

    padded_data = data + "0" * 32
    remainder = crc(padded_data, generator)
    codeword = data + remainder

    message_crc_var.set(remainder)
    message_codeword_var.set(codeword)
    message_length_var.set(str(len(codeword)))

    message_binary_text.config(state="normal")
    message_binary_text.delete("1.0", "end")
    message_binary_text.insert("1.0", data)
    message_binary_text.config(state="disabled")

    log("----- CLASSROOM MESSAGE -----")
    log("Message   : " + message)
    log("CRC-32    : " + remainder)
    log("Codeword  : " + codeword)
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

    messagebox.showinfo(
        "Report Generated",
        "CSV report saved successfully:\n" + file_name
    )


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
    file_result_var.set("WAITING FOR FILE VERIFICATION")

    message_crc_var.set("-")
    message_codeword_var.set("-")
    message_length_var.set("-")

    message_binary_text.config(state="normal")
    message_binary_text.delete("1.0", "end")
    message_binary_text.config(state="disabled")

    for item in result_tree.get_children():
        result_tree.delete(item)

    total_var.set("0")
    valid_var.set("0")
    corrupted_var.set("0")
    error_var.set("0")
    error_rate_var.set("0.00%")

    clear_log()


# ============================================================
# GUI
# ============================================================

root = tk.Tk()
root.title("Classroom Message Integrity Tool - CRC-32")
root.geometry("1250x900")
root.minsize(1050, 750)

# Variables
file_sender_var = tk.StringVar(value="No sender file selected")
file_sender_crc_var = tk.StringVar(value="-")
file_sender_size_var = tk.StringVar(value="-")

file_receiver_var = tk.StringVar(value="No receiver file selected")
file_receiver_crc_var = tk.StringVar(value="-")
file_receiver_size_var = tk.StringVar(value="-")
file_result_var = tk.StringVar(value="WAITING FOR FILE VERIFICATION")

message_crc_var = tk.StringVar(value="-")
message_codeword_var = tk.StringVar(value="-")
message_length_var = tk.StringVar(value="-")

total_var = tk.StringVar(value="0")
valid_var = tk.StringVar(value="0")
corrupted_var = tk.StringVar(value="0")
error_var = tk.StringVar(value="0")
error_rate_var = tk.StringVar(value="0.00%")


# Title
tk.Label(
    root,
    text="CLASSROOM MESSAGE INTEGRITY TOOL",
    font=("Arial", 22, "bold")
).pack(pady=(12, 2))

tk.Label(
    root,
    text="CRC-32 Based Error Detection | Text + Universal File Verification",
    font=("Arial", 11)
).pack(pady=(0, 8))


# ------------------------------------------------------------
# CLASSROOM MESSAGE
# ------------------------------------------------------------

message_frame = tk.LabelFrame(
    root,
    text="1. CLASSROOM MESSAGE - FACULTY",
    font=("Arial", 12, "bold"),
    padx=10,
    pady=8
)
message_frame.pack(fill="x", padx=20, pady=5)

tk.Label(
    message_frame,
    text="Announcement:"
).grid(row=0, column=0, sticky="w", padx=6, pady=4)

message_entry = tk.Entry(
    message_frame,
    width=80,
    font=("Arial", 11)
)
message_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=6)
message_entry.insert(0, "Exam will be conducted on Monday")

tk.Label(
    message_frame,
    text="33-bit CRC-32 Generator:"
).grid(row=1, column=0, sticky="w", padx=6, pady=4)

generator_entry = tk.Entry(
    message_frame,
    width=55,
    font=("Courier New", 10)
)
generator_entry.grid(row=1, column=1, sticky="w", padx=6)
generator_entry.insert(0, DEFAULT_GENERATOR)

tk.Button(
    message_frame,
    text="Calculate Message CRC-32",
    command=generate_message_crc,
    width=25
).grid(row=1, column=2, padx=6)

tk.Label(
    message_frame,
    text="Message CRC-32:"
).grid(row=2, column=0, sticky="w", padx=6)

tk.Label(
    message_frame,
    textvariable=message_crc_var,
    font=("Courier New", 10, "bold")
).grid(row=2, column=1, sticky="w", padx=6)

tk.Label(
    message_frame,
    text="Codeword Length:"
).grid(row=3, column=0, sticky="w", padx=6)

tk.Label(
    message_frame,
    textvariable=message_length_var
).grid(row=3, column=1, sticky="w", padx=6)

message_binary_text = tk.Text(
    message_frame,
    height=2,
    font=("Courier New", 8),
    wrap="none"
)
message_binary_text.grid(
    row=4, column=0, columnspan=3,
    sticky="ew", padx=6, pady=4
)
message_binary_text.config(state="disabled")


# ------------------------------------------------------------
# UNIVERSAL FILE INTEGRITY
# ------------------------------------------------------------

file_frame = tk.LabelFrame(
    root,
    text="2. UNIVERSAL FILE INTEGRITY - ALL FILE TYPES ACCEPTED",
    font=("Arial", 12, "bold"),
    padx=10,
    pady=8
)
file_frame.pack(fill="x", padx=20, pady=5)

tk.Label(
    file_frame,
    text="Original Sender File:"
).grid(row=0, column=0, sticky="w", padx=6, pady=4)

tk.Label(
    file_frame,
    textvariable=file_sender_var,
    font=("Arial", 10, "bold")
).grid(row=0, column=1, sticky="w", padx=6)

tk.Button(
    file_frame,
    text="SELECT ANY FILE",
    command=select_sender_file,
    width=20
).grid(row=0, column=2, padx=6)

tk.Label(
    file_frame,
    text="Sender CRC-32:"
).grid(row=1, column=0, sticky="w", padx=6)

tk.Label(
    file_frame,
    textvariable=file_sender_crc_var,
    font=("Courier New", 10, "bold")
).grid(row=1, column=1, sticky="w", padx=6)

tk.Label(
    file_frame,
    textvariable=file_sender_size_var
).grid(row=1, column=2, sticky="w", padx=6)

tk.Label(
    file_frame,
    text="Received File:"
).grid(row=2, column=0, sticky="w", padx=6, pady=4)

tk.Label(
    file_frame,
    textvariable=file_receiver_var,
    font=("Arial", 10, "bold")
).grid(row=2, column=1, sticky="w", padx=6)

tk.Button(
    file_frame,
    text="SELECT ANY RECEIVED FILE",
    command=verify_receiver_file,
    width=25
).grid(row=2, column=2, padx=6)

tk.Label(
    file_frame,
    text="Received CRC-32:"
).grid(row=3, column=0, sticky="w", padx=6)

tk.Label(
    file_frame,
    textvariable=file_receiver_crc_var,
    font=("Courier New", 10, "bold")
).grid(row=3, column=1, sticky="w", padx=6)

tk.Label(
    file_frame,
    textvariable=file_receiver_size_var
).grid(row=3, column=2, sticky="w", padx=6)

tk.Label(
    file_frame,
    textvariable=file_result_var,
    font=("Arial", 12, "bold")
).grid(
    row=4, column=0, columnspan=2,
    sticky="w", padx=6, pady=5
)

tk.Button(
    file_frame,
    text="BATCH VERIFY ANY FILES",
    command=batch_verify_files,
    width=25,
    height=2
).grid(row=4, column=2, padx=6)

tk.Label(
    file_frame,
    text="Accepted: PDF, Word, Excel, PowerPoint, JPG, PNG, MP4, ZIP, TXT and ANY other file.",
    font=("Arial", 9)
).grid(
    row=5, column=0, columnspan=3,
    sticky="w", padx=6, pady=2
)


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------

dashboard_frame = tk.LabelFrame(
    root,
    text="3. WORKING VERIFICATION DASHBOARD",
    font=("Arial", 12, "bold"),
    padx=8,
    pady=7
)
dashboard_frame.pack(fill="x", padx=20, pady=5)

for col in range(5):
    dashboard_frame.columnconfigure(col, weight=1)


def dashboard_card(title, variable, column):
    frame = tk.Frame(
        dashboard_frame,
        relief="groove",
        borderwidth=2,
        padx=10,
        pady=4
    )
    frame.grid(row=0, column=column, padx=4, sticky="nsew")

    tk.Label(
        frame,
        text=title,
        font=("Arial", 9, "bold")
    ).pack()

    tk.Label(
        frame,
        textvariable=variable,
        font=("Arial", 18, "bold")
    ).pack()


dashboard_card("TOTAL FILES", total_var, 0)
dashboard_card("VALID", valid_var, 1)
dashboard_card("CORRUPTED", corrupted_var, 2)
dashboard_card("ERROR", error_var, 3)
dashboard_card("ERROR RATE", error_rate_var, 4)


# ------------------------------------------------------------
# REPORT BUTTONS
# ------------------------------------------------------------

action_frame = tk.Frame(root)
action_frame.pack(fill="x", padx=20, pady=4)

tk.Button(
    action_frame,
    text="Generate CSV Report",
    command=generate_csv_report,
    width=22,
    height=2
).pack(side="left", padx=5)

tk.Button(
    action_frame,
    text="RESET",
    command=reset_all,
    width=12,
    height=2
).pack(side="right", padx=5)


# ------------------------------------------------------------
# RESULTS TABLE
# ------------------------------------------------------------

result_frame = tk.LabelFrame(
    root,
    text="4. BATCH VERIFICATION REPORT",
    font=("Arial", 12, "bold"),
    padx=6,
    pady=6
)
result_frame.pack(fill="both", expand=True, padx=20, pady=5)

columns = (
    "File Name",
    "File Type",
    "File Size",
    "Received CRC",
    "Status"
)

result_tree = ttk.Treeview(
    result_frame,
    columns=columns,
    show="headings",
    height=6
)

for column in columns:
    result_tree.heading(column, text=column)

result_tree.column("File Name", width=260)
result_tree.column("File Type", width=100)
result_tree.column("File Size", width=100)
result_tree.column("Received CRC", width=570)
result_tree.column("Status", width=130)

scrollbar = ttk.Scrollbar(
    result_frame,
    orient="vertical",
    command=result_tree.yview
)

result_tree.configure(yscrollcommand=scrollbar.set)

result_tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")


# ------------------------------------------------------------
# ACTIVITY LOG
# ------------------------------------------------------------

log_frame = tk.LabelFrame(
    root,
    text="Activity Log",
    font=("Arial", 11, "bold"),
    padx=6,
    pady=4
)
log_frame.pack(fill="x", padx=20, pady=4)

output_text = tk.Text(
    log_frame,
    height=5,
    state="disabled",
    font=("Courier New", 9)
)
output_text.pack(fill="x")


tk.Label(
    root,
    text="Faculty → Transmission Channel / Noise → Student → CRC-32 Verification → Dashboard → CSV Report",
    font=("Arial", 9)
).pack(pady=4)


root.mainloop()
