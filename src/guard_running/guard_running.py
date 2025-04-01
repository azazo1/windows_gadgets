import logging
import time
import os
import subprocess
import toml
import traceback
from pathlib import Path
import psutil

CONFIG_TOML = "guard_running_config.toml"
LOG_FILE = "guard_running.log"

PROCESS_NAME_KEY = "process_name"
LAUNCH_COMMAND_KEY = "launch_command"
GUARD_PAIR_KEY = "guard_pair"
INTERVAL_TIME_KEY = "interval_time"


def load_config(conf=CONFIG_TOML):
    """
    ```toml
    interval_time = 3

    [[guard_pair]]
    process_name = "proc_name.exe"
    launch_command = "path/to/executable.exe"

    [[guard_pair]]
    process_name = "proc_name_2.exe"
    launch_command = "path_2/to/executable_2.exe"
    ```
    """
    with open(conf, "r", encoding="utf-8") as r:
        rst = toml.load(r)
        print(rst)
    gp = rst[GUARD_PAIR_KEY]
    for p in gp:
        assert isinstance(p, dict)
        assert isinstance(p.get(LAUNCH_COMMAND_KEY), str)
        assert isinstance(p.get(INTERVAL_TIME_KEY), float) or isinstance(
            rst.get(INTERVAL_TIME_KEY), int
        )
    return rst


def find_process(name: str):
    for proc in psutil.process_iter(["name"]):
        try:
            proc_name = proc.info["name"]
            if proc_name == name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def main():
    os.chdir(Path(__file__).parent)
    try:
        os.remove(LOG_FILE)
    except FileNotFoundError:
        pass
    logger = logging.Logger(Path(__file__).stem)
    logger.addHandler(logging.FileHandler(LOG_FILE))
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    try:
        conf = load_config()
    except Exception:
        logger.error(traceback.format_exc())
        exit()
    gp = conf[GUARD_PAIR_KEY]
    interval = conf[INTERVAL_TIME_KEY]

    while True:
        try:
            for p in gp:
                pname = p[PROCESS_NAME_KEY]
                cmd = p[LAUNCH_COMMAND_KEY]
                if not find_process(pname):
                    subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    logger.info(f"Started new process: {cmd}")
        except Exception:
            err = traceback.format_exc()
            logger.error(err)
        time.sleep(interval)
