import enum
import math
import os
import socket
import traceback
import time
from pathlib import Path
from typing import Optional
import pynput
import pywinauto
import uiautomation
import win32con
import win32gui
import win32process
from screeninfo import get_monitors
from win32api import GetKeyboardLayout
import shutil

TEXT_EDITOR_EXE_PATH = "subl.exe"
VSCODE_EXE_PATH = "code"


class Direction(enum.Enum):
    UP = -90
    DOWN = 90
    LEFT = 180
    RIGHT = 0


TOTAL_HEIGHT = 0  # 所有屏幕高度的总和.
TOTAL_WIDTH = 0  # 所有屏幕宽度的总和.
SCREEN_DIAGONAL_SQUARE = TOTAL_WIDTH**2 + TOTAL_HEIGHT**2  # 对角线长度平方
# 由于主屏幕的位置不一定在左上角, 故可能有的窗口坐标为负, 要记录最左上方的屏幕坐标.
START_X = 0
START_Y = 0
END_X = 0
END_Y = 0

MIN_VALID_WINDOW_WIDTH = 30
MIN_VALID_WINDOW_HEIGHT = 30


def update_screen_size():
    global \
        TOTAL_WIDTH, \
        TOTAL_HEIGHT, \
        SCREEN_DIAGONAL_SQUARE, \
        END_X, \
        END_Y, \
        START_X, \
        START_Y
    for monitor in get_monitors():
        START_X = min(monitor.x, START_X)
        START_Y = min(monitor.y, START_Y)
        END_X = max(monitor.x + monitor.width, END_X)
        END_Y = max(monitor.y + monitor.height, END_Y)
    TOTAL_WIDTH = END_X - START_X
    TOTAL_HEIGHT = END_Y - START_Y
    SCREEN_DIAGONAL_SQUARE = TOTAL_WIDTH**2 + TOTAL_HEIGHT**2


def get_center(rect):
    return rect.left + rect.width() / 2, rect.top + rect.height() / 2


def get_window_center(window):
    return get_center(window.rectangle())


def is_valid(desktop, window):
    if not window.is_visible():
        return False
    if not window.window_text():
        return False
    rect = window.rectangle()
    center = get_center(rect)
    if center[0] < START_X or center[0] > END_X:
        return False
    if center[1] < START_Y or center[1] > END_Y:
        return False
    top_window = desktop.top_from_point(*(int(p) for p in center))
    if top_window != window:
        return False
    return (  # 不完全超出屏幕.
        window.is_maximized()
        or rect.right >= START_X
        and rect.bottom >= START_Y
        and rect.left <= END_X
        and rect.top <= END_Y
        and MIN_VALID_WINDOW_WIDTH <= rect.width() <= TOTAL_WIDTH
        and MIN_VALID_WINDOW_HEIGHT <= rect.height() <= TOTAL_HEIGHT
    )


def select_focused(valid_windows):
    for window in valid_windows:
        if window.has_focus():
            return window


def calc_angles(valid_windows, target_window):
    """
    :param valid_windows: 可以包括 valid_windows.
    """
    window_rel_angles = []
    raw_point = get_window_center(target_window)
    for window in valid_windows:
        if window != target_window:
            center = get_window_center(window)
            angle = math.atan2(center[1] - raw_point[1], center[0] - raw_point[0])
            angle = angle * 180 / math.pi  # 转换为角度
            window_rel_angles.append((window, angle))
    return window_rel_angles


def switch_to(direction: Direction):
    update_screen_size()
    try:
        desktop = pywinauto.Desktop(backend="win32")
        windows = desktop.windows()
    except Exception as _:
        traceback.print_exc()
        return
    valid_windows = [window for window in windows if is_valid(desktop, window)]
    focused_window = select_focused(valid_windows)
    if focused_window is None:
        if valid_windows:
            focus_on_window(
                valid_windows[0]
            )  # 可能原焦点在桌面, 那么随机选一个窗口聚焦.
        return
    window_rel_angles = calc_angles(valid_windows, focused_window)
    focused_window_center = get_window_center(focused_window)
    print(direction, window_rel_angles)
    # 选出和指定方向最近的 window.
    selected_window = None
    min_weight = None
    for window, angle in window_rel_angles:
        if direction == Direction.LEFT:
            # 向左的时候, 有 180 和 -180 度两种可能, 用 abs 消除两者差距.
            angle_diff_ratio = abs(direction.value - abs(angle)) / 180
        else:
            angle_diff_ratio = abs(direction.value - angle) / 180
        center = get_window_center(window)
        distance_square_ratio = (
            (focused_window_center[0] - center[0]) ** 2
            + (focused_window_center[1] - center[1]) ** 2
        ) / SCREEN_DIAGONAL_SQUARE  # 归一化.
        weight = distance_square_ratio * 0.6 + angle_diff_ratio * 0.4
        if min_weight is None or weight < min_weight:
            selected_window = window
            min_weight = weight
    if selected_window is None:
        return
    focus_on_window(selected_window)
    print("Switched to", selected_window.window_text())


def focus_on_window(window):
    ctl = uiautomation.ControlFromHandle(window.handle)
    ctl.SetFocus()  # 这种获取焦点的方式不会改变窗口大小.
    pynput.mouse.Controller().position = get_window_center(window)


def open_text_editor():
    os.startfile(TEXT_EDITOR_EXE_PATH)


def open_vscode():
    path = shutil.which(VSCODE_EXE_PATH)
    if not path:
        return
    path = Path(path)
    if path.parent.name == "bin":
        # look for code.exe instead of code.cmd
        path = path.parent.parent / "Code.exe"
    os.startfile(path)


def get_vk(key):
    if isinstance(key, pynput.keyboard.Key):
        return key.value.vk
    elif isinstance(key, pynput.keyboard._win32.KeyCode):
        return key.vk
    elif isinstance(key, pynput.keyboard.KeyCode):
        return key.vk
    else:
        return None


def get_input_method():
    """
    Returns:
        - 1033 是英文输入法.
        - 2052 是微软拼音输入法.
    """
    hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
        # 获取当前线程的键盘布局 (HKL)
        current_layout = GetKeyboardLayout(thread_id)
        layout_id = current_layout & 0x0000FFFF
        return layout_id
    return None


def switch_input_method(locale):
    if locale < 0:
        return
    hwnd = win32gui.GetForegroundWindow()
    win32gui.PostMessage(hwnd, win32con.WM_INPUTLANGCHANGEREQUEST, 0, locale)


def switch_im():
    if get_input_method() == 1033:
        switch_input_method(2052)
    else:
        switch_input_method(1033)


listener: Optional[pynput.keyboard.Listener] = None
caps_lock_pressing = False
lshift_pressing = False
pending_vk_code = None
operations = (
    False  # 在按下 capslock 的时候有没有执行操作(比如使用 capslock + l 切换窗口焦点)
)


def win32_event_filter(msg, data):
    global caps_lock_pressing, pending_vk_code, lshift_pressing, operations
    is_pressing = not bool(data.flags & (1 << 7))
    if pending_vk_code == data.vkCode:
        if is_pressing:  # 取消长按产生的重复事件.
            if caps_lock_pressing:
                listener.suppress_event()
            return
        else:  # 消除按键松开事件.
            pending_vk_code = None
            listener.suppress_event()

    if data.vkCode == get_vk(pynput.keyboard.Key.caps_lock):
        if caps_lock_pressing != is_pressing:  # capslock 键按下状态发生变化.
            print(f"Caps lock: {is_pressing}")
            caps_lock_pressing = is_pressing
            if is_pressing:
                operations = False
            elif (
                not operations
            ):  # capslock 松开, 但是没有按下其他键, 相当于直接按下了 capslock.
                print("Switch IME ")
                switch_im()
        listener.suppress_event()
    elif data.vkCode == get_vk(pynput.keyboard.Key.shift_l):
        if lshift_pressing != is_pressing:
            print(f"LShift: {is_pressing}")
        lshift_pressing = is_pressing
        operations = True
    elif data.vkCode == get_vk(pynput.keyboard.Key.left) or data.vkCode == 0x48:  # h
        if caps_lock_pressing and is_pressing:
            pending_vk_code = data.vkCode
            operations = True
            switch_to(Direction.LEFT)
            listener.suppress_event()
    elif data.vkCode == get_vk(pynput.keyboard.Key.right) or data.vkCode == 0x4C:  # l
        if caps_lock_pressing and is_pressing:
            pending_vk_code = data.vkCode
            operations = True
            switch_to(Direction.RIGHT)
            listener.suppress_event()
    elif data.vkCode == get_vk(pynput.keyboard.Key.up) or data.vkCode == 0x4B:  # k
        if caps_lock_pressing and lshift_pressing and is_pressing:
            # 鼠标滚轮功能.
            operations = True
            pynput.keyboard.Controller().release(
                pynput.keyboard.Key.shift_l
            )  # 注意在按下 shift 的时候鼠标滚轮无效, 于是暂时取消 shift 按下.
            pynput.mouse.Controller().scroll(0, 1)
            pynput.keyboard.Controller().press(
                pynput.keyboard.Key.shift_l
            )  # 注意在按下 shift 的时候鼠标滚轮无效.
            listener.suppress_event()
        elif caps_lock_pressing and is_pressing:
            pending_vk_code = data.vkCode
            operations = True
            switch_to(Direction.UP)
            listener.suppress_event()
    elif data.vkCode == get_vk(pynput.keyboard.Key.down) or data.vkCode == 0x4A:  # j
        if caps_lock_pressing and lshift_pressing and is_pressing:
            # 鼠标滚轮功能.
            operations = True
            pynput.keyboard.Controller().release(
                pynput.keyboard.Key.shift_l
            )  # 注意在按下 shift 的时候鼠标滚轮无效, 于是暂时取消 shift 按下.
            pynput.mouse.Controller().scroll(0, -1)
            pynput.keyboard.Controller().press(pynput.keyboard.Key.shift_l)
            listener.suppress_event()
        elif caps_lock_pressing and is_pressing:
            pending_vk_code = data.vkCode
            operations = True
            switch_to(Direction.DOWN)
            listener.suppress_event()
    elif data.vkCode == 0x45:  # e
        if caps_lock_pressing and is_pressing:
            pending_vk_code = data.vkCode
            operations = True
            open_text_editor()
            listener.suppress_event()
    elif data.vkCode == 0x56:  # v
        if caps_lock_pressing and is_pressing:
            pending_vk_code = data.vkCode
            operations = True
            open_vscode()
            listener.suppress_event()


def main():
    os.chdir(Path(__file__).parent)
    global listener
    try:
        with socket.create_server(("127.0.0.1", 23982)):  # 单一实例.
            with pynput.keyboard.Listener(
                win32_event_filter=win32_event_filter
            ) as listener:
                listener.join()
    except Exception:
        with open(Path(__file__).with_suffix(".log"), "a") as w:
            w.write("\n")
            w.write(time.asctime())
            w.write(traceback.format_exc())
