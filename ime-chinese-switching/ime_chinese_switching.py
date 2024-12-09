"""
参考自: https://github.com/PEMessage/im-select-imm/blob/imm/src/im-select-imm.cpp
"""
import logging
import traceback
from pathlib import Path
import ctypes
import time
import win32con
import win32gui
import win32process
from win32api import GetKeyboardLayout, PostMessage, SendMessage

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


def get_input_mode():
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


def main():
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                        filename=f"{Path(__file__).stem}.log",
                        level=logging.DEBUG)
    logging.info("Script start")
    while True:
        try:
            method = get_input_method()
            mode = get_input_mode()
            if method == 2052 and mode & 0x01 == 0:
                switch_input_mode(1)
            time.sleep(0.1)
        except Exception:
            logging.error(traceback.format_exc())


if __name__ == '__main__':
    main()
