import requests
from pathlib import Path
import json
import time

from pytermite.connection import (
    WiredConnection
)

def fetch_recorded( serials: dict[str, str] | set[str] | None = None, 
                    save_path: str|None = None, 
                    logger = None
    ):
    logger_available = logger is not None
    if (serials is None or len(serials) < 1):
        if logger_available:
            logger.warning("No connected GoPros found! Recorded data could not be fetched")
        return

    if save_path is None:
        save_path = Path.home() / "Downloads"
    else:
        save_path = Path(save_path)

    for serial_nr in serials:
        ip = f"172.2{serial_nr[-3]}.1{serial_nr[-2:]}.51:8080"

        url_last = f"http://{ip}/gopro/media/last_captured"
        response_last = requests.request("GET", url_last)

        response_data = json.loads(response_last.text)
        if response_last.status_code == 200:
            url_info = f"http://{ip}/gopro/media/info"
            querystring = {"path":f"{response_data["folder"]}/{response_data["file"]}"}

            counter = 0
            while counter < 10:
                response = json.loads(requests.request("GET", url, params=querystring).text)
                if response["tr"] == 1:
                    break
                counter += 1
                time.sleep(1)

            url = f"http://{ip}/videos/DCIM/{response_data["folder"]}/{response_data["file"]}"
            response = requests.request("GET", url)
            with open(save_path / response_data["file"], "wb") as f:
                f.write(response.content)

        elif logger_available:
            # TODO: How to map on name of cam? Might be more readable
            logger.warning(f"Last recorded data from serial: {serial_nr} could not be fetched") 