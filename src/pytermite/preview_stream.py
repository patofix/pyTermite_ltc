import requests
import tkinter as tk
import threading
import math
import asyncio
import subprocess
import tempfile

class PreviewStream():
    def __init__(self, serials, stop_event, logger):
        self.logger = logger
        self.serials = serials
        self.stop_event = stop_event
        #self.ports = [int(f"855{i}") for i in range(len(self.serials))]
        #self.ips = {f"172.2{serial_nr[-3]}.1{serial_nr[-2:]}.51:8080": self.ports[idx] for idx, serial_nr in enumerate(self.serials)}
        self.ips = {}
        self.root = tk.Tk()
        self.canvas_size = math.ceil(math.sqrt(len(serials)))
        self.canvas = canvas = tk.Canvas(self.root, width=1000, height=1000, bg="white")
        self.canvas.grid(row=self.canvas_size, column=self.canvas_size)
        self.preview_start()
        self.root.mainloop()
    
    def preview_start(self) -> None:
        #for ip, port in self.ips.items():
        #    #print(requests.get(f"http://{ip}/gopro/camera/state").json())
        #    url = f"http://{ip}/gopro/camera/stream/start"
        #    response = requests.request("GET", url)
        for connection in self.serials:
            url = f"https://{connection.ip_address}/gopro/camera/stream/start"
            cert_string = connection.cohn.credentials.certificate
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
                f.write(cert_string)
                cert_path = f.name
            auth = (connection.cohn.credentials.username, connection.cohn.credentials.password)
            response = requests.request("GET", url, verify=cert_path, auth=auth)
            print(response)
            self.ips[connection.ip_address] = 8556
        total_canvas_width = self.canvas.winfo_width()
        asyncio.run(self.show_streams(total_canvas_width))

    def preview_stop(self) -> None:
        for ip in self.ips:
            url = f"http://{ip}/gopro/camera/stream/stop"
            response = requests.request("GET", url)
    
    async def show_streams(self, total_canvas_width):
        loop = asyncio.get_event_loop()
        for ip, port in self.ips.items():
            row, col = divmod(port % 10, 3) 
            threading.Thread(target=UDPReceiver, args=(self.canvas, row, col, ip, port, self.canvas_size, total_canvas_width), daemon=True).start()
        await self.stop_event.wait()


class UDPReceiver():
    def __init__(self, canvas, row, col, ip, port, canvas_size, total_canvas_width):
        super().__init__()
        self.canvas = canvas
        self.row = row
        self.column = col
        self.ip = ip
        self.port = port
        self.canvas_size = canvas_size
        self.total_canvas_width = total_canvas_width
        self._run()
    
    def _run(self):
        #TODO check whether duplicating this (width, height, framesize) inside loop make it responsive to window changes during runtime
        width = self.total_canvas_width // self.canvas_size
        height = (width * 9) // 16
        frame_size = width * height * 3
        process = subprocess.Popen(["ffmpeg", "-i", f"udp://{self.ip}:8556", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"], stdout=subprocess.PIPE)
        while raw_bytes := process.stdout.read(frame_size):
            image = PIL.Image.frombytes("RGB", (width, height), raw_bytes)
            imageTk = ImageTk.PhotoImage(image)
            self.canvas.after(0, lambda img=imageTk: self.canvas.create_image(self.column * width, self.row * height, image=img))