import psutil
import time
import win32gui
import win32process
import ctypes

# Đổi tên file .bat ở đây
BAT_NAME = "test.bat"

# API gốc từ User32.dll
IsHungAppWindow = ctypes.windll.user32.IsHungAppWindow

def kill_all_bat():
    killed = []
    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        try:
            if proc.info["name"].lower() == "cmd.exe":
                cmdline = " ".join(proc.info["cmdline"]).lower()
                if BAT_NAME.lower() in cmdline:
                    proc.kill()
                    killed.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return killed

def find_bat():
    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        try:
            if proc.info["name"].lower() == "cmd.exe":
                cmdline = " ".join(proc.info["cmdline"]).lower()
                if BAT_NAME.lower() in cmdline:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def is_window_not_responding(pid):
    """Kiểm tra nếu cửa sổ thuộc tiến trình PID bị Not Responding"""
    hwnds = []

    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                hwnds.append(hwnd)
        return True

    win32gui.EnumWindows(callback, None)

    for hwnd in hwnds:
        if IsHungAppWindow(hwnd):  # != 0 nếu treo
            return True
    return False

def monitor_and_wait():
    while True:
        proc = None
        print(f"Đang chờ {BAT_NAME} được bật...")
        while proc is None:
            proc = find_bat()
            time.sleep(2)

        print(f"[+] Đã phát hiện {BAT_NAME} (PID={proc.pid})")

        not_resp_count = 0

        while True:
            time.sleep(2)
            if proc.is_running():
                if is_window_not_responding(proc.pid):
                    not_resp_count += 1
                    print(f"[STATUS] {BAT_NAME} Not Responding ({not_resp_count}/5)")
                    if not_resp_count >= 5:  # sau 5 lần (10s) thì kill
                        print(f"[!] {BAT_NAME} bị treo >10s → Kill")
                        proc.kill()
                        break
                else:
                    not_resp_count = 0
                    print(f"[STATUS] {BAT_NAME} hoạt động bình thường")
            else:
                print(f"[STATUS] {BAT_NAME} đã thoát")
                break

if __name__ == "__main__":
    killed_pids = kill_all_bat()
    if killed_pids:
        print(f"[+] Đã tắt các {BAT_NAME} cũ PID={killed_pids}")
    else:
        print(f"[+] Không có {BAT_NAME} nào chạy trước đó")

    monitor_and_wait()
