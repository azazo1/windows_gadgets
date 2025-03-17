"""
此脚本把剪贴板中的中文标点替换为英文的标点加一个空格.
"""

import os
from pathlib import Path
import time
from typing import Optional

import pyperclip

chPunc = "，《。》、？；：“”【】！￥（）—"
enPunc = [
    ", ",
    "<",
    ". ",
    ">",
    ", ",
    "? ",
    "; ",
    ": ",
    ' "',
    '" ',
    "[",
    "]",
    "! ",
    "$",
    " (",
    ") ",
    "--",
]
extra_space = {
    ") .": ").",
    ") ,": "),",
    ': "': ':"',
}


def hasChPunc(content: str) -> Optional[tuple[int, int]]:
    for i, ch in enumerate(chPunc):
        idx = content.find(ch)
        if idx != -1:
            return i, idx  # 字符在 map 中的位置, 字符在内容中的位置
    return None


def wait_for_new_paste(interval=2):
    origin = pyperclip.paste()
    while True:
        time.sleep(interval)
        new = pyperclip.paste()
        if new != origin:
            break
    return new


def main():
    os.chdir(Path(__file__).parent)
    first = True
    while True:
        if first:
            rawContent = content = pyperclip.paste()
        else:
            rawContent = content = wait_for_new_paste(0.3)
        first = False
        if not content:
            continue
        print(f'Get Content: {{ "{content}" }}.')
        while (rst := hasChPunc(content)) is not None:
            i, idx = rst
            content = content.replace(chPunc[i], enPunc[i], 1)

        for es, vl in extra_space.items():
            content = content.replace(es, vl)

        if content != rawContent:
            print(f'Converted To: {{ "{content}" }}.')
            pyperclip.copy(content)
