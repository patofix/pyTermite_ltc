import os
import time
import re
import subprocess

"""
Basic usb handling functions used for timecode recordings
"""

#  Copyright (c) 2026 by Jonas Rostan
#
#  SPDX-License-Identifier: BSD-3-Clause

def activate_ports(usb_ports = None):
    return _handle_usb_bind(usb_ports)

def deactivate_ports(usb_ports = None):
    return _handle_usb_bind(usb_ports, bind=False)

def _handle_usb_bind(usb_ports=None, bind=True, allowed_retries=5) -> bool:
    if usb_ports is None: return False
    for port in usb_ports:
        retry = 0
        while retry < allowed_retries:
            output = subprocess.run(f"echo '{port}' | sudo tee /sys/bus/usb/drivers/usb/{"bind" if bind else "unbind"}", shell=True, capture_output=True)
            if "busy" not in output.stderr.decode():
                break
            retry += 1
            time.sleep(1)
        if retry >= allowed_retries:
            return False
    return True

def get_usbports(serials) -> set[str]:
    ports = set()
    for serial_nr in serials:
        ip = f"172.2{serial_nr[-3]}.1{serial_nr[-2:]}.51:8080"
        usb_port = _get_usbport_by_ip(ip)
        if usb_port is None: continue
        ports.add(usb_port)
    return ports

def _get_usbport_by_ip(gopro_ip: str) -> str | None:
    net_dir = "/sys/class/net"
    if not os.path.exists(net_dir):
        return None

    for interface in os.listdir(net_dir):
        device_link = os.path.join(net_dir, interface, "device")
        if not os.path.islink(device_link):
            continue
        
        real_path = os.path.realpath(device_link)
        if "usb" not in real_path:
            continue

        match = re.search(r'/usb\d+/([^/:\s]+)', real_path)
        if not match:
            continue

        usb_port = match.group(1)

        try:
            output = subprocess.check_output(["ip", "route", "show", "dev", interface], text=True)

            subnet_prefix = ".".join(gopro_ip.split(".")[:2])
            if subnet_prefix in output:
                return usb_port
        except subprocess.SubprocessError:
            continue

    return None