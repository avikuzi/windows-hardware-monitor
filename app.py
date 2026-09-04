"""
Real-Time Hardware Monitoring & Diagnostic Dashboard
Built with Streamlit, psutil, WMI, and Plotly.
Diagnoses CPU Overheating & Explorer Downloads Lag.
"""

import time
import os
import platform
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# Import custom telemetry & advisor modules
from telemetry.cpu import CPUTelemetry
from telemetry.memory import MemoryTelemetry
from telemetry.disk import DiskTelemetry
from telemetry.diagnostics import DownloadsDiagnostic
from advisor.engine import SmartAdvisorEngine

# Streamlit Page Config
st.set_page_config(
    page_title="Hardware Diagnostics & Thermal Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Cyberpunk / Hardware Monitor Aesthetic)
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e222d 0%, #151821 100%);
        border: 1px solid #2d3343;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .metric-header {
        font-size: 0.85rem;
        color: #8a99ad;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f3f4f6;
    }
    .badge-critical {
        background-color: #ef4444;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-warning {
        background-color: #f59e0b;
        color: black;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-optimal {
        background-color: #10b981;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
        display: inline-block;
    }
    .advisory-box {
        background-color: #1a1e29;
        border-left: 5px solid #3b82f6;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 14px;
    }
    .advisory-critical { border-left-color: #ef4444 !important; }
    .advisory-warning { border-left-color: #f59e0b !important; }
    .advisory-optimal { border-left-color: #10b981 !important; }
</style>
""", unsafe_allow_html=True)


# Initialize Session State Objects
if "cpu_telemetry" not in st.session_state:
    st.session_state.cpu_telemetry = CPUTelemetry()
if "mem_telemetry" not in st.session_state:
    st.session_state.mem_telemetry = MemoryTelemetry()
if "disk_telemetry" not in st.session_state:
    st.session_state.disk_telemetry = DiskTelemetry()
if "downloads_diag" not in st.session_state:
    st.session_state.downloads_diag = DownloadsDiagnostic()
if "advisor_engine" not in st.session_state:
    st.session_state.advisor_engine = SmartAdvisorEngine()
if "history" not in st.session_state:
    st.session_state.history = {
        "timestamps": [],
        "cpu_load": [],
        "disk_read": [],
        "disk_write": [],
        "ram_load": []
    }

# Sidebar Controls
st.sidebar.title("⚡ Hardware Monitor")
st.sidebar.markdown(f"**Host:** `{platform.node()}`")
st.sidebar.markdown(f"**OS:** `{platform.system()} {platform.release()}`")

refresh_rate = st.sidebar.slider("Auto-Refresh Interval (Seconds)", min_value=1, max_value=10, value=2)
enable_refresh = st.sidebar.toggle("Enable Live Auto-Refresh", value=True)

# Diagnostic Simulation Mode (for testing advice under severe conditions)
st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Fault Simulation Mode")
simulate_overheat = st.sidebar.checkbox("Simulate CPU Overheat (>92°C & Throttle)", value=False)
simulate_disk_lag = st.sidebar.checkbox("Simulate Downloads Folder Lag (450ms & Queue > 3)", value=False)

# Auto-refresh handling
try:
    from streamlit_autorefresh import st_autorefresh
    if enable_refresh:
        st_autorefresh(interval=refresh_rate * 1000, key="data_refresher")
except ImportError:
    # Fallback to sleep + rerun
    if enable_refresh:
        time.sleep(refresh_rate)
        st.rerun()

# -------------------------------------------------------------
# COLLECT REAL-TIME TELEMETRY DATA
# -------------------------------------------------------------
cpu_data = st.session_state.cpu_telemetry.get_cpu_metrics()
mem_data = st.session_state.mem_telemetry.get_memory_metrics()
disk_data = st.session_state.disk_telemetry.get_disk_metrics()
diag_data = st.session_state.downloads_diag.run_benchmark_and_audit()

# Apply simulation overrides if selected
if simulate_overheat:
    cpu_data["package_temp"] = 94.5
    cpu_data["is_throttling"] = True
    cpu_data["throttle_severity"] = "CRITICAL"
    cpu_data["throttle_reason"] = "Simulation: Severe Thermal Throttling triggered at 94.5°C"
    cpu_data["current_freq_mhz"] = min(cpu_data["current_freq_mhz"], 1200.0)

if simulate_disk_lag:
    diag_data["scan_latency_ms"] = 482.0
    diag_data["folder_template"] = "Media (Forced Thumbnail Generation!)"
    diag_data["total_files"] = 1250
    diag_data["thumbnail_cache_size_mb"] = 420.0
    diag_data["incomplete_downloads"] = 4
    diag_data["executables_count"] = 85
    disk_data["queue_length"] = 3.8
    disk_data["active_time_percent"] = 98.2

# Store History
curr_time_str = time.strftime("%H:%M:%S")
st.session_state.history["timestamps"].append(curr_time_str)
st.session_state.history["cpu_load"].append(cpu_data["total_percent"])
st.session_state.history["disk_read"].append(disk_data["read_mb_s"])
st.session_state.history["disk_write"].append(disk_data["write_mb_s"])
st.session_state.history["ram_load"].append(mem_data["ram_percent"])

# Keep max 40 historical points
for key in st.session_state.history:
    st.session_state.history[key] = st.session_state.history[key][-40:]

# -------------------------------------------------------------
# SMART ADVISOR EVALUATION
# -------------------------------------------------------------
advisories = st.session_state.advisor_engine.evaluate(
    cpu_metrics=cpu_data,
    disk_metrics=disk_data,
    mem_metrics=mem_data,
    diagnostics=diag_data
)

# -------------------------------------------------------------
# MAIN DASHBOARD UI
# -------------------------------------------------------------
st.title("🖥️ PC Hardware Diagnostics & Telemetry Dashboard")
st.markdown("Real-time telemetry and rule-based diagnostic advisor for CPU Thermals and Windows File Explorer bottlenecks.")

# Top Status Indicators
status_col1, status_col2, status_col3 = st.columns(3)

has_critical = any(a.severity == "CRITICAL" for a in advisories)
has_warning = any(a.severity == "WARNING" for a in advisories)

with status_col1:
    if has_critical:
        st.markdown('<div class="badge-critical">⚠️ CRITICAL HARDWARE ATTENTION REQUIRED</div>', unsafe_allow_html=True)
    elif has_warning:
        st.markdown('<div class="badge-warning">⚡ SYSTEM PERFORMANCE WARNING</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge-optimal">✅ SYSTEM STATUS OPTIMAL</div>', unsafe_allow_html=True)

with status_col2:
    if cpu_data["is_throttling"]:
        st.markdown('<div class="badge-critical">🔥 CPU THERMAL THROTTLING ACTIVE</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge-optimal">❄️ CPU CLOCKS NORMAL</div>', unsafe_allow_html=True)

with status_col3:
    if diag_data.get("is_severe_lag", False):
        st.markdown('<div class="badge-warning">📂 DOWNLOADS FOLDER LATENCY HIGH</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge-optimal">🚀 DISK I/O LATENCY HEALTHY</div>', unsafe_allow_html=True)

st.markdown("---")

# =============================================================
# SECTION 1: TELEMETRY METRIC TILES
# =============================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-header">CPU Package Temp</div>', unsafe_allow_html=True)
    pkg_temp = cpu_data["package_temp"]
    temp_str = f"{pkg_temp}°C" if pkg_temp is not None else "N/A"
    temp_color = "#ef4444" if (pkg_temp and pkg_temp >= 85) else ("#f59e0b" if (pkg_temp and pkg_temp >= 75) else "#10b981")
    st.markdown(f'<div class="metric-value" style="color:{temp_color};">{temp_str}</div>', unsafe_allow_html=True)
    st.caption(f"Sensor Source: {cpu_data['temperature_data']['source']}")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-header">CPU Core Load & Clock</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{cpu_data["total_percent"]}%</div>', unsafe_allow_html=True)
    st.caption(f"Clock: {cpu_data['current_freq_mhz']:.0f} MHz / {cpu_data['max_freq_mhz']:.0f} MHz")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-header">Disk I/O Throughput</div>', unsafe_allow_html=True)
    total_io = disk_data["total_throughput_mb_s"]
    st.markdown(f'<div class="metric-value">{total_io} <span style="font-size:1rem;">MB/s</span></div>', unsafe_allow_html=True)
    st.caption(f"Read: {disk_data['read_mb_s']} MB/s | Write: {disk_data['write_mb_s']} MB/s")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-header">Disk Active Time & Queue</div>', unsafe_allow_html=True)
    act_pct = disk_data["active_time_percent"]
    q_len = disk_data["queue_length"]
    q_color = "#ef4444" if (act_pct >= 90 or q_len >= 2.0) else "#10b981"
    st.markdown(f'<div class="metric-value" style="color:{q_color};">{act_pct:.1f}%</div>', unsafe_allow_html=True)
    st.caption(f"Queue Length: {q_len:.2f} ({disk_data['wmi_status']})")
    st.markdown('</div>', unsafe_allow_html=True)

# Memory quick row
mcol1, mcol2, mcol3, mcol4 = st.columns(4)
with mcol1:
    st.metric("RAM Used", f"{mem_data['used_ram_gb']} GB", f"{mem_data['ram_percent']}% of {mem_data['total_ram_gb']} GB")
with mcol2:
    st.metric("RAM Available", f"{mem_data['available_ram_gb']} GB")
with mcol3:
    st.metric("Pagefile (Swap) Used", f"{mem_data['used_swap_gb']} GB", f"{mem_data['swap_percent']}%")
with mcol4:
    st.metric("Downloads Traversal Latency", f"{diag_data['scan_latency_ms']} ms", f"{diag_data['total_files']} files")

st.markdown("---")

# =============================================================
# SECTION 2: SMART ADVISOR EXPERT SYSTEM
# =============================================================
st.header("🧠 Smart Hardware Advisor & Actionable Solutions")
st.markdown("The rule engine continuously evaluates CPU thermal ceilings, throttling ratios, and Explorer I/O bottlenecks.")

for adv in advisories:
    adv_class = "advisory-box"
    if adv.severity == "CRITICAL":
        adv_class += " advisory-critical"
    elif adv.severity == "WARNING":
        adv_class += " advisory-warning"
    elif adv.severity == "OPTIMAL":
        adv_class += " advisory-optimal"

    with st.container():
        st.markdown(f"""
        <div class="{adv_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; color:#f3f4f6;">{adv.title}</h4>
                <span class="badge-{adv.severity.lower()}">{adv.severity}</span>
            </div>
            <p style="margin-top:6px; margin-bottom:4px; color:#cbd5e1;"><strong>Problem:</strong> {adv.problem}</p>
            <p style="margin-bottom:8px; color:#94a3b8;"><strong>Root Cause Analysis:</strong> {adv.root_cause}</p>
        </div>
        """, unsafe_allow_html=True)

        expander_title = f"🛠️ Step-by-Step Fixes for: {adv.title}"
        with st.expander(expander_title, expanded=(adv.severity in ["CRITICAL", "WARNING"])):
            tcol1, tcol2 = st.columns(2)
            with tcol1:
                st.markdown("**🔧 Hardware Engineering Recommendations:**")
                st.info(adv.hardware_advice)
            with tcol2:
                st.markdown("**💻 Windows OS & Software Tuning:**")
                st.warning(adv.software_advice)

            if adv.powershell_fix:
                st.markdown("**⚡ Automated PowerShell Fix Script:**")
                st.code(adv.powershell_fix, language="powershell")

st.markdown("---")

# =============================================================
# SECTION 3: DEEP DIVE - CORE ISSUES
# =============================================================
tab_cpu, tab_disk, tab_charts = st.tabs(["🔥 Issue 1: CPU Thermals & Throttling", "📂 Issue 2: Downloads Directory Lag", "📊 Real-Time Charts"])

# ----------------- TAB 1: CPU THERMAL DEEP DIVE -----------------
with tab_cpu:
    st.subheader("CPU Thermal & Frequency Analysis")
    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("#### Thermal Throttling Status")
        if cpu_data["is_throttling"]:
            st.error(f"⚠️ **ACTIVE THROTTLING DETECTED:** {cpu_data['throttle_reason']}")
        elif cpu_data["throttle_severity"] == "WARNING":
            st.warning(f"⚠️ **ELEVATED HEAT:** {cpu_data['throttle_reason']}")
        else:
            st.success("✅ **CPU Cooling Optimal:** Frequency and temperature are operating within safe thermal junctions.")

        st.markdown(f"- **Physical Cores:** `{cpu_data['physical_cores']}` | **Logical Cores:** `{cpu_data['logical_cores']}`")
        st.markdown(f"- **Current Clock:** `{cpu_data['current_freq_mhz']:.0f} MHz` (Rated Max: `{cpu_data['max_freq_mhz']:.0f} MHz`)")
        if cpu_data["package_temp"]:
            st.markdown(f"- **Package Temperature:** `{cpu_data['package_temp']} °C`")
        
        # Per core load progress bars
        st.markdown("#### Per-Core Utilization")
        per_core = cpu_data.get("per_core_percent", [])
        for idx, core_load in enumerate(per_core):
            st.progress(core_load / 100.0, text=f"Core #{idx}: {core_load}%")

    with c2:
        st.markdown("#### Top CPU Consuming Processes")
        if cpu_data["top_processes"]:
            df_proc = pd.DataFrame(cpu_data["top_processes"])
            df_proc.columns = ["PID", "Process Name", "CPU %", "RAM %"]
            st.dataframe(df_proc, use_container_width=True, hide_index=True)
        else:
            st.info("Process metrics polling in progress...")

        st.markdown("#### Hardware Engineer Checklist for CPU Overheating:")
        st.markdown("""
        - [ ] **Thermal Paste Replacement:** Paste dries out after 2-3 years. Clean with 99% Isopropyl alcohol and apply dot or cross pattern.
        - [ ] **AIO Liquid Cooler Health:** If CPU instantly hits 90°C under light load, pump impellers may be jammed or air-locked.
        - [ ] **Mounting Standoffs:** Uneven thumbscrew tension leads to convex/concave contact gaps.
        - [ ] **Plastic Film Check:** Ensure protective peel on heatsink copper base was removed.
        - [ ] **BIOS Voltage Overprovisioning:** Many Z-series/X-series motherboards push up to 1.45V+ by default. Set Lite Load / LLC to normal.
        """)

# ----------------- TAB 2: DOWNLOADS DIRECTORY LAG DEEP DIVE -----------------
with tab_disk:
    st.subheader("Windows Explorer Downloads Directory Profiler")
    st.markdown(f"Inspecting Directory: `{diag_data['path']}`")

    dcol1, dcol2 = st.columns([1, 1])

    with dcol1:
        st.markdown("#### Audit & Metadata Metrics")
        st.markdown(f"- **Directory Scan Time:** `{diag_data['scan_latency_ms']} ms` {'⚠️ (High)' if diag_data['scan_latency_ms'] > 300 else '✅ (Fast)'}")
        st.markdown(f"- **Read Probe Latency:** `{diag_data['read_latency_ms']} ms`")
        st.markdown(f"- **Total Files:** `{diag_data['total_files']}`")
        st.markdown(f"- **Total Folders:** `{diag_data['total_folders']}`")
        st.markdown(f"- **Total Directory Size:** `{diag_data['total_size_mb']:.1f} MB`")
        st.markdown(f"- **Folder Optimization Template:** `{diag_data['folder_template']}`")
        st.markdown(f"- **Windows Thumbnail Cache Size:** `{diag_data['thumbnail_cache_size_mb']} MB`")

        st.markdown("#### File Distribution:")
        dist_df = pd.DataFrame([
            {"Category": "Executables (.exe, .msi, .bat)", "Count": diag_data["executables_count"]},
            {"Category": "Archives (.zip, .rar, .7z)", "Count": diag_data["archives_count"]},
            {"Category": "Media Files (Pictures/Videos)", "Count": diag_data["media_count"]},
            {"Category": "Incomplete Downloads (.crdownload, .tmp)", "Count": diag_data["incomplete_downloads"]}
        ])
        st.dataframe(dist_df, use_container_width=True, hide_index=True)

    with dcol2:
        st.markdown("#### Why Windows Explorer Hangs on Downloads:")
        st.markdown("""
        1. **Automatic Folder Optimization Misclassification:**
           Windows Explorer tries to be smart. When it sees images or setup files, it changes the folder view to **Pictures** or **Videos**. This causes Explorer to crawl every file to build thumbnails and read metadata tags, causing severe disk thrashing.
        2. **Corrupted Thumbnail Cache Database:**
           `thumbcache_*.db` files get corrupted by unexpected reboots or file locks, making Explorer lock the UI thread while attempting to query the database.
        3. **Antivirus Real-Time Shell Scanning:**
           Every `.exe` and `.zip` file enumerated in Downloads gets intercepted by Windows Defender or 3rd party AV.
        """)

        st.markdown("#### 1-Click Fix Instructions:")
        st.markdown("""
        **Method 1 (GUI):**
        1. Open File Explorer, right-click **Downloads** -> **Properties**.
        2. Click the **Customize** tab.
        3. Under *Optimize this folder for:*, select **General items**.
        4. Check the box: **Also apply this template to all subfolders**.
        5. Click **Apply** -> **OK**.

        **Method 2 (PowerShell Quick Fix):**
        Run PowerShell as Administrator and execute:
        """)
        st.code("""
# Reset Downloads folder template to General Items
$desktopIni = "$HOME\\Downloads\\desktop.ini"
if (Test-Path $desktopIni) {
    attrib -h -s $desktopIni
    Remove-Item -Force $desktopIni
}
# Purge corrupt thumbnail cache database
taskkill /f /im explorer.exe
Get-ChildItem -Path "$env:LOCALAPPDATA\\Microsoft\\Windows\\Explorer" -Filter thumbcache_*.db | Remove-Item -Force
start explorer.exe
        """, language="powershell")

# ----------------- TAB 3: REAL-TIME CHARTS -----------------
with tab_charts:
    st.subheader("Live Telemetry Trends")
    t1, t2 = st.columns(2)

    with t1:
        fig_cpu = go.Figure()
        fig_cpu.add_trace(go.Scatter(
            x=st.session_state.history["timestamps"],
            y=st.session_state.history["cpu_load"],
            mode="lines+markers",
            name="CPU Load %",
            line=dict(color="#3b82f6", width=2)
        ))
        fig_cpu.add_trace(go.Scatter(
            x=st.session_state.history["timestamps"],
            y=st.session_state.history["ram_load"],
            mode="lines",
            name="RAM Load %",
            line=dict(color="#10b981", width=2, dash="dot")
        ))
        fig_cpu.update_layout(
            title="CPU & RAM Utilization (%)",
            yaxis=dict(range=[0, 100]),
            template="plotly_dark",
            margin=dict(l=20, r=20, t=40, b=20),
            height=300
        )
        st.plotly_chart(fig_cpu, use_container_width=True)

    with t2:
        fig_disk = go.Figure()
        fig_disk.add_trace(go.Scatter(
            x=st.session_state.history["timestamps"],
            y=st.session_state.history["disk_read"],
            mode="lines+markers",
            name="Read MB/s",
            line=dict(color="#06b6d4", width=2)
        ))
        fig_disk.add_trace(go.Scatter(
            x=st.session_state.history["timestamps"],
            y=st.session_state.history["disk_write"],
            mode="lines",
            name="Write MB/s",
            line=dict(color="#f43f5e", width=2)
        ))
        fig_disk.update_layout(
            title="Disk Throughput (MB/s)",
            template="plotly_dark",
            margin=dict(l=20, r=20, t=40, b=20),
            height=300
        )
        st.plotly_chart(fig_disk, use_container_width=True)
