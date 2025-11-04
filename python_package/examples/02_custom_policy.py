"""
Example 2: Custom Policy
=========================
This example shows how to implement a custom control policy in Python.
"""
import pylite3
import numpy as np
import time
import os
import threading
import sys, termios, tty, select
try:
    from pynput import keyboard   # pip install pynput
except Exception as e:
    keyboard = None
    print("[!] Không tìm thấy pynput (pip install pynput). Sẽ dùng chế độ fallback bằng stdin.")


try:
    import onnxruntime
except ImportError:
    print("onnxruntime is not installed. Please install it with: pip install onnxruntime")
    exit(1)

FREQ_HZ = 100.0                   # tần số điều khiển loop C++
VX_SCALE = 0.7                    # hệ số tốc tiến/lùi (0..1)
VY_SCALE = 0.6                    # hệ số strafe trái/phải (0..1)
VYAW_SCALE = 0.7                  # hệ số quay (0..1)
SMOOTHING = 0.15                  # 0..1, càng lớn chuyển mượt hơn

# ====== Biến trạng thái điều khiển từ bàn phím ======
_cmd_lock = threading.Lock()
_target_vx = 0.0
_target_vy = 0.0
_target_wz = 0.0
_cur_vx = 0.0
_cur_vy = 0.0
_cur_wz = 0.0
_running = True

def clamp(x, lo=-1.0, hi=1.0): return max(lo, min(hi, x))

def _apply_smoothing(cur, target, alpha):
    return cur + (target - cur) * alpha

def _update_robot_velocity(robot):
    global _cur_vx, _cur_vy, _cur_wz
    with _cmd_lock:
        _cur_vx = _apply_smoothing(_cur_vx, _target_vx, SMOOTHING)
        _cur_vy = _apply_smoothing(_cur_vy, _target_vy, SMOOTHING)
        _cur_wz = _apply_smoothing(_cur_wz, _target_wz, SMOOTHING)
        robot.set_velocity(clamp(_cur_vx), clamp(_cur_vy), clamp(_cur_wz))
    print(f"[UPDATE] vx: {_cur_vx}, vy: {_cur_vy}, wz: {_cur_wz}")
    if _cur_vx != _target_vx:
            print(f"Warning: _cur_vx({_cur_vx}) != _target_vx({_target_vx})")
    robot.set_velocity(clamp(_cur_vx), clamp(_cur_vy), clamp(_cur_wz))
    state = robot.get_state()
    print(f"[STATE] cmd_vel_norm: {state.cmd_vel_normlized}")

def _set_targets(vx=None, vy=None, wz=None):
    global _target_vx, _target_vy, _target_wz
    with _cmd_lock:
        if vx is not None: _target_vx = clamp(vx)
        if vy is not None: _target_vy = clamp(vy)
        if wz is not None: _target_wz = clamp(wz)

def _reset_axis(axis):
    if axis == "vx": _set_targets(vx=0.0)
    if axis == "vy": _set_targets(vy=0.0)
    if axis == "wz": _set_targets(wz=0.0)

# ====== Bàn phím: pynput ======
def _on_press(key):
    try: k = key.char.lower()
    except: k = str(key)
    if k == 'w': _set_targets(vx=+VX_SCALE)
    elif k == 's': _set_targets(vx=-VX_SCALE)
    elif k == 'a': _set_targets(wz=+VYAW_SCALE)
    elif k == 'd': _set_targets(wz=-VYAW_SCALE)

def _on_release(key):
    global _running
    try: k = key.char.lower()
    except: k = str(key)
    if k in ('w', 's'): _reset_axis("vx")
    elif k in ('a', 'd'): _reset_axis("wz")
    elif k in ('Key.esc',): _running = False
    # giữ lại các phím khác

def _keyboard_thread():
    with keyboard.Listener(on_press=_on_press, on_release=_on_release) as listener:
        listener.join()

# ====== Fallback stdin ======
def _stdin_raw_thread(robot):
    global _running
    print("[RAW] WSAD quay/tiến-lùi, Q/E strafe, X dừng, ESC thoát (không cần Enter).")
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)  # Hoặc tty.setraw(fd)
        while _running:
            r, _, _ = select.select([sys.stdin], [], [], 0.05)
            if not r:
                continue
            ch = sys.stdin.read(1)
            if not ch:
                continue
            c = ch.lower()
            if c == 'w': 
                print("Pressed W, setting vx to", VX_SCALE)
                _set_targets(vx=+VX_SCALE)  # Gửi lệnh tăng tiến
            elif c == 's': 
                print("Pressed S, setting vx to", -VX_SCALE)
                _set_targets(vx=-VX_SCALE)  # Gửi lệnh giảm tiến
            elif c == 'a': 
                print("Pressed A, setting wz to", +VYAW_SCALE)
                _set_targets(wz=+VYAW_SCALE)  # Gửi lệnh quay trái
            elif c == 'd': 
                print("Pressed D, setting wz to", -VYAW_SCALE)
                _set_targets(wz=-VYAW_SCALE)  # Gửi lệnh quay phải
            elif c == 'q': 
                print("Pressed Q, setting vy to", +VY_SCALE)
                _set_targets(vy=+VY_SCALE)  # Strafe trái
            elif c == 'e': 
                print("Pressed E, setting vy to", -VY_SCALE)
                _set_targets(vy=-VY_SCALE)  # Strafe phải
            elif c == 'x': 
                print("Pressed X, stopping all motion")
                _set_targets(vx=0.0, vy=0.0, wz=0.0)  # Dừng tất cả
            elif ch == '\x1b':  # ESC để thoát
                print("ESC pressed, exiting.")
                _set_targets(0.0, 0.0, 0.0)
                break
            _update_robot_velocity(robot)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        _running = False   

def main():
    print("=== Example 2: Custom Policy ===\n")
    global _running
    global _cur_vx, _cur_vy, _cur_wz
    # Create robot controller
    robot = pylite3.Lite3Controller(use_sim=True)

    # --- 1. Khởi tạo chính sách tùy chỉnh của chúng ta ---
    # Chính sách này sẽ tải mô hình ONNX và xử lý logic điều khiển.
    model_path = "../../policy/ppo/policy.onnx"

    # Stand up
    print("Standing up...")
    robot.stand_up(duration=5.0, blocking=True)
    time.sleep(1.0)

    # --- 2. Thiết lập chính sách tùy chỉnh và chạy robot ---
    print("Setting and running custom ONNX policy...")
    # Truyền đối tượng chính sách vào robot.
    # Giờ đây, hàm __call__ của OnnxGaitPolicy sẽ được gọi ở tần số 50Hz.
    # Đặt tần số về 50Hz để phù hợp với tần suất huấn luyện của mô hình.
    robot.load_onnx_policy(model_path)
    robot.run_async(pylite3.ControlMode.RL_CONTROL)

    if keyboard is not None:
        t = threading.Thread(target=_keyboard_thread, daemon=True)
        t.start()
        print("Điều khiển: W/S tiến-lùi, A/D quay, Q/E strafe, Esc để thoát.")
    else:
        t = threading.Thread(target=_stdin_raw_thread, daemon=True)
        t.start()

    # Vòng lặp cập nhật vận tốc gửi sang controller
    try:
        while _running:
            _stdin_raw_thread(robot)
            # _update_robot_velocity(robot)
            # time.sleep(0.02)  # 50 Hz cập nhật lệnh, loop C++ chạy 100 Hz
    except KeyboardInterrupt:
        pass
    finally:
        _set_targets(0,0,0)
#       gửi vài nhịp 0 để robot dừng mượt
        for _ in range(10):
            _update_robot_velocity(robot)
            time.sleep(0.02)
        robot.stop()
        print("Đã dừng robot. Bye!")
    print("Example complete!")

if __name__ == "__main__":
    main()
