import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Classroom Message Integrity Tool", page_icon="🔐", layout="wide")

DEFAULT_GENERATOR = "100000100110000010001110110110111"

def crc(data, generator):
    r = len(generator) - 1
    work = list(map(int, data + "0" * r))
    gen = list(map(int, generator))
    for i in range(len(work) - r):
        if work[i] == 1:
            for j in range(len(gen)):
                work[i + j] ^= gen[j]
    return "".join(map(str, work[-r:]))

def bytes_to_binary(data):
    return "".join(format(b, "08b") for b in data)

def text_to_binary(text):
    return bytes_to_binary(text.encode("utf-8"))

def file_crc(data, generator):
    return crc(bytes_to_binary(data), generator)

st.title("🔐 Classroom Message Integrity Tool")
st.caption("CRC-32 based message and file integrity verification dashboard")

with st.sidebar:
    st.header("⚙️ CRC Configuration")
    generator = st.text_input("33-bit Generator Polynomial", DEFAULT_GENERATOR).strip()
    if len(generator) != 33 or any(c not in "01" for c in generator):
        st.error("Generator must contain exactly 33 binary digits.")
        st.stop()
    st.info("Any file type is accepted: PDF, DOCX, XLSX, PPTX, JPG, PNG, ZIP, etc.")

if "results" not in st.session_state:
    st.session_state.results = []

tab1, tab2, tab3 = st.tabs(["💬 Classroom Message", "📁 File Integrity", "📊 Dashboard & Report"])

with tab1:
    st.subheader("Classroom Message CRC-32")
    message = st.text_area("Enter classroom announcement / timetable / exam message", height=130)
    if st.button("Calculate Message CRC", type="primary"):
        if not message.strip():
            st.warning("Please enter a message.")
        else:
            binary = text_to_binary(message)
            checksum = crc(binary, generator)
            a, b = st.columns(2)
            a.metric("Message Length", f"{len(message)} characters")
            b.metric("CRC-32", checksum)
            with st.expander("View Binary Data"):
                st.code(binary)

with tab2:
    st.subheader("Universal File Integrity Verification")
    sender = st.file_uploader("1️⃣ Select Original Sender File", key="sender")
    if sender:
        sender_data = sender.getvalue()
        sender_crc = file_crc(sender_data, generator)

        a, b, c = st.columns(3)
        a.metric("Sender File", sender.name)
        b.metric("File Size", f"{len(sender_data):,} bytes")
        c.metric("Sender CRC-32", sender_crc)

        received = st.file_uploader(
            "2️⃣ Select Received File(s) for Batch Verification",
            accept_multiple_files=True, key="received"
        )

        if received and st.button("Verify Selected Files", type="primary"):
            rows = []
            for f in received:
                data = f.getvalue()
                try:
                    rcrc = file_crc(data, generator)
                    status = "VALID" if rcrc == sender_crc else "CORRUPTED"
                    err = ""
                except Exception as e:
                    rcrc, status, err = "", "ERROR", str(e)
                rows.append({
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "File Name": f.name, "File Type": f.type or "Unknown",
                    "File Size": len(data), "Sender CRC": sender_crc,
                    "Received CRC": rcrc, "Status": status, "Error": err
                })
            st.session_state.results.extend(rows)
            st.success(f"Verified {len(rows)} file(s).")

        if received:
            preview = []
            for f in received:
                data = f.getvalue()
                rcrc = file_crc(data, generator)
                preview.append({"File Name": f.name, "File Size": len(data),
                                "Received CRC": rcrc,
                                "Status": "VALID" if rcrc == sender_crc else "CORRUPTED"})
            st.write(preview)

        st.caption("Use a copy of the same original file to test VALID. A modified copy should show CORRUPTED.")

with tab3:
    st.subheader("📊 Verification Dashboard")
    df = pd.DataFrame(st.session_state.results)
    total = len(df)
    valid = int((df["Status"] == "VALID").sum()) if total else 0
    corrupted = int((df["Status"] == "CORRUPTED").sum()) if total else 0
    errors = int((df["Status"] == "ERROR").sum()) if total else 0
    rate = corrupted / total * 100 if total else 0

    a, b, c, d, e = st.columns(5)
    a.metric("Total Verified", total)
    b.metric("✅ Valid", valid)
    c.metric("❌ Corrupted", corrupted)
    d.metric("⚠️ Errors", errors)
    e.metric("Error Rate", f"{rate:.1f}%")

    if total:
        st.write(df.to_dict("records"))
        st.download_button(
            "⬇️ Download CSV Verification Report",
            df.to_csv(index=False).encode("utf-8"),
            "crc32_verification_report.csv", "text/csv"
        )
        if st.button("Clear Dashboard"):
            st.session_state.results = []
            st.rerun()
    else:
        st.info("No verification records yet.")

st.divider()
st.caption("CRC-32 Classroom Message Integrity Tool • Batch Verification • CSV Reporting")
