import logging
import time
import traceback

import pynput.keyboard
import uiautomation

_taskbar = uiautomation.PaneControl(Depth=1, Name="任务栏", ClassName="Shell_TrayWnd")


class ReserveCursorFocus:
    """
    在执行某个操作后恢复鼠标指针位置和焦点.

    Examples:

    >>> # 1
    >>> with ReserveCursorFocus():
    ...     print("Hello World") # 替换成其他会改变鼠标位置或者焦点的操作.
    Hello World
    >>> # 2
    >>> reserve = ReserveCursorFocus()
    >>> reserve.save() # 此行可选, 也可调用多次.
    >>> print("Hello World") # 替换成其他会改变鼠标位置或者焦点的操作.
    Hello World
    >>> reserve.restore() # 此行可调用多次.
    """

    def __init__(self, reserve_cursor=True, reserve_focus=True):
        """
        Parameters:
            reserve_cursor: 是否保存鼠标位置.
            reserve_focus: 是否保存焦点.
        """
        self.reserve_cursor = reserve_cursor
        self.reserve_focus = reserve_focus
        self.cursor: tuple[int, int] = (-1, -1)
        self.focus: int = -1
        self.save()

    def save(self):
        self.cursor = uiautomation.GetCursorPos()
        self.focus = uiautomation.GetForegroundWindow()

    def restore(self):
        if self.reserve_focus:
            uiautomation.ControlFromHandle(self.focus).SetFocus()
        if self.reserve_cursor:
            uiautomation.SetCursorPos(*self.cursor)
        time.sleep(0.1)  # 确保焦点已经完全转移, 否则再次调用 GetForegroundWindow 会返回 None.

    def __enter__(self):
        self.save()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore()


def get_taskbar() -> uiautomation.PaneControl:
    """
    获取任务栏控件.
    """
    _taskbar.Refind(0, 0)
    return _taskbar


def get_ms_ch_ime_button() -> uiautomation.Control:
    """
    获取微软拼音输入法中文输入法按钮控件.

    - 如果输入法语言只有一种, 此按钮不会出现, 返回 None.
    - 如果当前输入法不是微软系统中文输入法, 返回 None.
    """

    def cmp_func(control: uiautomation.Control, depth: int):
        return all((
            isinstance(control, uiautomation.ButtonControl),
            control.ClassName == "SystemTray.NormalButton",
            control.AutomationId == "SystemTrayIcon",
            depth == 3,
            control.Name == '托盘输入指示器 中文(简体，中国)\r\n微软拼音\r\n\r\n要切换输入法，按 Windows 键+空格。'
        ))

    return uiautomation.FindControl(get_taskbar(), cmp_func, 3)  # FindControl 不会缓存搜索, 都是直接搜索.


def get_en_mode_button() -> uiautomation.Control:
    """
    获取微软拼音输入法英语模式按钮.
    """

    def cmp_func(control: uiautomation.Control, depth: int):
        return all((
            isinstance(control, uiautomation.ButtonControl),
            control.ClassName == "SystemTray.NormalButton",
            control.AutomationId == "SystemTrayIcon",
            depth == 3,
            control.Name == '托盘输入指示器 英语模式\n\n单击右键以查看更多选项'
        ))

    return uiautomation.FindControl(get_taskbar(), cmp_func, 3)


def main():
    controller = pynput.keyboard.Controller()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)
    while True:
        try:
            ime = get_ms_ch_ime_button()
            en = get_en_mode_button()
            if ime and en:
                controller.press(pynput.keyboard.Key.ctrl_l)
                time.sleep(0.1)
                controller.release(pynput.keyboard.Key.ctrl_l)
                logging.info("switched")
            time.sleep(0.4)
        except Exception:
            logging.error(traceback.format_exc())


if __name__ == '__main__':
    main()
