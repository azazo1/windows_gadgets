"""
参考自: https://github.com/PEMessage/im-select-imm/blob/imm/src/im-select-imm.cpp
"""
import logging
import traceback
from pathlib import Path
import ctypes
import time
from typing import Callable
import sys
import subprocess

import win32con
import win32gui
import win32process
from win32api import GetKeyboardLayout, PostMessage, SendMessage

IME_RESETTING = True
ESCAPE_SWITCHING = True

# NI_CONTEXTUPDATED 查看 immdev.h 发现以下内容, 但是在 learn microsoft 文档中没有记录:
IMC_SETCONVERSIONMODE = 0x0002
IMC_SETSENTENCEMODE = 0x0004
IMC_SETOPENSTATUS = 0x0006


# 获取当前输入法布局（返回低 16 位的布局标识符）
def get_input_method():
    """
    Returns:
        - 1033 是英文输入法.
        - 2052 是微软拼音输入法.
    """
    hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
        # 获取当前线程的键盘布局（HKL）
        current_layout = GetKeyboardLayout(thread_id)
        layout_id = current_layout & 0x0000FFFF
        return layout_id
    return None


def switch_input_mode(mode):
    if mode < 0:
        return
    foreground_window = win32gui.GetForegroundWindow()
    foreground_ime = ctypes.windll.imm32.ImmGetDefaultIMEWnd(foreground_window)
    if foreground_ime:
        SendMessage(foreground_ime, win32con.WM_IME_CONTROL, IMC_SETCONVERSIONMODE, mode)


def get_input_mode() -> int | None:
    """
    API: https://learn.microsoft.com/en-us/previous-versions/aa913780(v=msdn.10)
    对于 Microsoft 旧版中文输入法（Windows 10 及之前）:
          0: 英文
          1: 中文
    对于 Microsoft 新版中文输入法（Windows 11）:
          0: 英文 / 半角
          1: 中文 / 半角
          1024: 英文 / 全角（Bit10 和 Bit1 用于表示）
          1025: 中文 / 全角
    """
    foreground_window = win32gui.GetForegroundWindow()
    foreground_ime = ctypes.windll.imm32.ImmGetDefaultIMEWnd(foreground_window)
    if foreground_ime:
        result = SendMessage(foreground_ime, win32con.WM_IME_CONTROL, 0x01, 0)
        return result
    return None


def switch_input_method(locale):
    if locale < 0:
        return
    hwnd = win32gui.GetForegroundWindow()
    PostMessage(hwnd, win32con.WM_INPUTLANGCHANGEREQUEST, 0, locale)


prev_foreground_window = win32gui.GetForegroundWindow()


def ime_resetting():
    """
    当焦点窗口变化的时候, 重置输入法为英文输入法(1033).
    """
    global prev_foreground_window
    foreground_window = win32gui.GetForegroundWindow()
    if prev_foreground_window != foreground_window:
        prev_foreground_window = foreground_window
        switch_input_method(1033)
        prev_foreground_window = foreground_window


def register_escape_switching():
    """
    注册 Ctrl + [ 快捷键切换输入法.
    """
    from pynput import keyboard
    from threading import Thread
    
    def on_activate():
        switch_input_method(1033)
    
    def listen_hotkey():
        with keyboard.GlobalHotKeys({
            '<ctrl>+[': on_activate
        }) as h:
            h.join()
    
    # 启动热键监听线程
    hotkey_thread = Thread(target=listen_hotkey, daemon=True)
    hotkey_thread.start()


class Restarter:
    FILE_LOCK = "restart.lock"

    def __init__(self):
        self.lock = Path(__file__).parent.joinpath(self.FILE_LOCK).resolve()

    def clear_lock(self):
        self.lock.unlink(missing_ok=True)

    def should_restart(self):
        with open(self.lock, "a+") as r:
            r.seek(0)
            if "restart" in r.read():
                return True
        return False

    def notify_restart(self, timeout=1):
        if not self.lock.exists():
            self.lock.touch(exist_ok=True)
            return
        with open(self.lock, "w") as w:
            w.write("restart")
        start_time = time.time()
        while time.time() - start_time < timeout and self.lock.exists():
            time.sleep(0.3)
        with open(self.lock, "w"):
            pass


class Throttler:
    def __init__(self, func: Callable, interval: float, /, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.interval = interval
        self.last_time = 0

    def __call__(self):
        now = time.time()
        if now - self.last_time >= self.interval:
            rst = self.func(*self.args, **self.kwargs)
            self.last_time = now
            return rst
        return None

    def throttle(self):
        return self()


def init_logging():
    path = Path(__file__).resolve()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    s_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(path.with_suffix(".log"))
    s_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(s_handler)
    logger.addHandler(f_handler)


def self_restart():
    if getattr(sys, "frozen", False):
        subprocess.Popen([sys.executable, *sys.argv[1:]])
    else:
        subprocess.Popen([sys.executable, *sys.argv])
    raise KeyboardInterrupt()


def main():
    path = Path(__file__).resolve()
    init_logging()
    logging.info(f"Script start: {path}")
    logging.info("Restart checking...")
    restarter = Restarter()
    restarter.notify_restart()
    logging.info("Restart checked")
    logging.info(f"Script running...")
    should_restart = Throttler(restarter.should_restart, 1)
    ticker = Throttler(lambda: print(f"Ticking {time.asctime()}"), 5)

    if ESCAPE_SWITCHING:
        register_escape_switching()
    try:
        while True:
            try:
                method = get_input_method()
                mode = get_input_mode()
                if method == 2052 and mode & 0x01 == 0:
                    switch_input_mode(1)
                if IME_RESETTING:
                    ime_resetting()
                if should_restart():
                    break
                ticker()
                time.sleep(0.1)
            except Exception:
                logging.error(traceback.format_exc())
                # self_restart()
    finally:
        restarter.clear_lock()


if __name__ == '__main__':
    main()
