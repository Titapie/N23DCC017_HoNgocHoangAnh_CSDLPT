# ==============================================================================
# HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT)
# ĐỒ ÁN MÔN HỌC: CƠ SỞ DỮ LIỆU PHÂN TÁN
#
# Đề tài 105: Merkle Tree Log Integrity: "Immutable Audit Trail"
# Sinh viên thực hiện: Hồ Ngọc Hoàng Anh
# Mã số sinh viên: N23DCCN071
# Lớp: D23CQCN01-N
#
# Tệp tin: run_all.py - Script điều phối khởi chạy đồng thời tất cả các Flask nodes
# ==============================================================================
import subprocess
import sys
import os
import time

def run_services():
    processes = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define services: (name, script, port)
    services = [
        ("Trusted Third Party (TTP)", "nodes/ttp.py", 5003),
        ("Site A (Clean Copy)", "nodes/site_a.py", 5001),
        ("Site B (Attacked Copy)", "nodes/site_b.py", 5002),
        ("Coordinator & Web UI", "nodes/coordinator.py", 5000),
    ]

    print("==================================================")
    print("      LAUNCHING DISTRIBUTED DATABASE NODES        ")
    print("==================================================")

    # Helper to clean/check databases
    data_dir = os.path.join(current_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print("[+] Created data directory for SQLite files.")

    # Determine the python executable to use.
    # If a virtual environment (.venv) exists in the project root, use its python.
    venv_python = os.path.join(current_dir, ".venv", "bin", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = os.path.join(current_dir, ".venv", "Scripts", "python.exe")
    
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable

    try:
        # Start each subprocess
        for name, script, port in services:
            script_path = os.path.join(current_dir, script)
            print(f"[i] Starting {name} on port {port}...")
            
            p = subprocess.Popen(
                [python_exe, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            processes.append((name, p))
            time.sleep(0.5)  # brief delay to prevent port binding collisions

        print("\n[+] All nodes launched successfully!")
        print("--------------------------------------------------")
        print(" -> Web Dashboard:  http://127.0.0.1:5000")
        print(" -> Site A API   :  http://127.0.0.1:5001")
        print(" -> Site B API   :  http://127.0.0.1:5002")
        print(" -> TTP API      :  http://127.0.0.1:5003")
        print("--------------------------------------------------")
        print("[*] Press Ctrl+C to terminate all services.")
        
        while True:
            for name, p in processes:
                poll = p.poll()
                if poll is not None:
                    print(f"\n[!] WARNING: {name} terminated unexpectedly with exit code {poll}.")
                    out, _ = p.communicate()
                    print(f"Logs:\n{out}")
                    raise KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[i] Terminating all services...")
        for name, p in processes:
            print(f"  Stopping {name}...")
            p.terminate()
            p.wait()
        print("[+] All services stopped clean. Goodbye!")

if __name__ == '__main__':
    run_services()
