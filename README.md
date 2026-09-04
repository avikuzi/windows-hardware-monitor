# ⚡ PC Hardware Diagnostics & Telemetry Dashboard

A real-time, modular hardware monitoring and diagnostic dashboard tailored for Windows. It is specifically engineered to diagnose:
1. **Severe CPU Overheating & Thermal Throttling**
2. **Extreme Windows File Explorer Lag / Freezing in the "Downloads" Directory**
3. **Storage I/O Saturation & Memory Exhaustion**

---

## 🏗️ Architecture & Module Breakdown

The project follows a clean, modular structure:

```
c:\Users\aviku\OneDrive\Documents\HW\
│
├── requirements.txt            # Python dependencies (Streamlit, psutil, wmi, pywin32, plotly)
├── run.bat                     # 1-Click launcher with auto-venv setup
├── app.py                      # Real-time Streamlit dashboard UI
│
├── telemetry\
│   ├── __init__.py
│   ├── cpu.py                  # CPU load, per-core metrics, frequencies, WMI/LHM thermal sensors & throttle detector
│   ├── memory.py               # RAM and Pagefile/Swap memory metrics
│   ├── disk.py                 # Real-time Read/Write speeds (MB/s), Disk Active Time %, and Queue Length
│   └── diagnostics.py          # Dedicated Downloads folder latency profiler & Windows shell audit
│
└── advisor\
    ├── __init__.py
    └── engine.py               # Rule-based expert system with hardware & software recommendations
```

---

## 🎯 How the Core Issues Are Diagnosed & Fixed

### 1. Severe CPU Overheating & Thermal Throttling
- **Telemetry Collected**:
  - Package Temperature (°C) via multiple Windows channels (LibreHardwareMonitor WMI, OpenHardwareMonitor WMI, and Windows ACPI `MSAcpi_ThermalZoneTemperature`).
  - Core Frequencies (Current vs. Base/Max MHz).
  - CPU Core Utilization (% load per physical/logical core).
  - Top 5 CPU-consuming processes.
- **Throttling Detection Logic**:
  - Flags **ACTIVE THROTTLING** when temperature exceeds TjMax threshold (>88°C-92°C) or when frequencies drop severely (<80% rated clock) despite heavy CPU load (>70%).
- **Hardware Engineer Advice**:
  - Thermal paste repasting (thermal pump-out effect).
  - AIO liquid cooler impeller/cavitation inspection.
  - Mounting bracket torque and heatsink peel check.
  - BIOS fan curve tuning (100% PWM at 80°C) and CPU undervolting (-0.050V offset).

---

### 2. Windows Explorer "Downloads" Directory Hanging & Lag
- **Telemetry Collected**:
  - Directory traversal and enumeration latency (`os.scandir` in milliseconds).
  - Random read I/O latency probe on folder items.
  - Disk Queue Length and Active Time % from Windows Performance Counters.
  - Folder template optimization check (`desktop.ini` inspection).
  - Windows Thumbnail Database size (`thumbcache_*.db`).
  - File distribution (Executables, Archives, Media, and stuck `.crdownload` / `.tmp` files).
- **Root Causes Diagnosed**:
  1. **Folder Template Misclassification**: Windows Explorer automatically sets the folder to "Pictures" or "Videos", forcing thumbnail extraction on non-media files.
  2. **Corrupted Thumbnail Cache**: Bloated `thumbcache_*.db` locking the Explorer UI thread.
  3. **Antivirus / Defender Shell Interception**: Scanning every `.exe` and `.zip` upon folder load.
- **Automated Fix**:
  - The dashboard provides a copy-paste PowerShell script to reset folder templates to **General Items** and safely purge corrupt thumbnail caches.

---

## 🚀 Step-by-Step Execution Guide

### Prerequisites
- Windows 10 or Windows 11
- Python 3.10 or higher installed with **Add Python to PATH** enabled.

---

### Option A: Quick 1-Click Launch (Recommended)
Double-click `run.bat` in File Explorer, or execute it in Command Prompt:
```cmd
run.bat
```
This automatically initializes a virtual environment, installs requirements, and launches the dashboard.

---

### Option B: Manual Setup via Terminal

1. **Open PowerShell or Command Prompt** in the project directory:
   ```cmd
   cd c:\Users\aviku\OneDrive\Documents\HW
   ```

2. **Create and Activate a Virtual Environment**:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```cmd
   pip install -r requirements.txt
   ```

4. **Launch the Dashboard**:
   ```cmd
   streamlit run app.py
   ```

5. **Access the Web Dashboard**:
   Open your browser and navigate to:
   ```
   http://localhost:8501
   ```

---

## 💡 Pro-Tips for Windows Hardware Access
- **Thermal Sensors**: For direct hardware sensor registers (per-core temps, VRM temps), running the terminal or batch file as **Administrator** gives WMI elevated permissions. You can also run **LibreHardwareMonitor** in the background, which exposes full sensor trees to WMI.
- **Fault Simulation**: Use the sidebar toggles (**Simulate CPU Overheat** / **Simulate Downloads Folder Lag**) to test the Smart Advisor's reaction to worst-case hardware failures even while your PC is idle.
