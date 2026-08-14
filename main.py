import ssl

ssl._create_default_https_context = ssl._create_unverified_context

import flet as ft
import socket
import requests
import os
import threading
import tkinter as tk
from tkinter import filedialog

from network import Discovery, get_my_ip
from server import start_server_in_background


def main(page: ft.Page):
    # UI Configuration
    page.title = "Jhotpot Share - Local File Transfer"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    try:
        page.window.width = 420
        page.window.height = 700
    except Exception:
        pass

    my_ip = get_my_ip()
    my_name = socket.gethostname()

    # Start Background Receiver Server
    start_server_in_background(port=5000)

    selected_file_path = [None]
    discovered_ips = set()
    device_list = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO)

    def show_toast(message):
        snack = ft.SnackBar(content=ft.Text(message), open=True)
        page.overlay.append(snack)
        page.update()

    selected_file_text = ft.Text("No file selected", color="grey", size=13)

    # Windows Native File Picker
    def open_native_file_picker(e):
        def pick():
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            filepath = filedialog.askopenfilename()
            root.destroy()

            if filepath:
                selected_file_path[0] = filepath
                filename = os.path.basename(filepath)
                selected_file_text.value = f"Selected: {filename}"
                selected_file_text.color = "green"
            else:
                selected_file_path[0] = None
                selected_file_text.value = "No file selected"
                selected_file_text.color = "grey"
            page.update()

        threading.Thread(target=pick, daemon=True).start()

    # File Transfer Logic
    def send_file_to(target_ip):
        if not selected_file_path[0]:
            show_toast("⚠️ Please select a file first!")
            return

        filepath = selected_file_path[0]
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)

        show_toast(f"Sending: {filename}...")

        def upload_thread():
            try:
                with open(filepath, 'rb') as f:
                    headers = {
                        'File-Name': filename,
                        'Content-Length': str(file_size)
                    }
                    response = requests.post(f"http://{target_ip}:5000", data=f, headers=headers, timeout=120)
                    if response.status_code == 200:
                        show_toast("File sent successfully! 🎉")
                    else:
                        show_toast("Failed to send file!")
            except Exception as err:
                show_toast(f"Transfer error: {err}")

        threading.Thread(target=upload_thread, daemon=True).start()

    # On New Device Discovered
    def on_device_found(dev_name, dev_ip):
        if dev_ip not in discovered_ips:
            discovered_ips.add(dev_ip)
            device_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=12,
                        content=ft.Row([
                            ft.Icon(ft.Icons.DEVICES, color="blue", size=28),
                            ft.Column([
                                ft.Text(dev_name, weight=ft.FontWeight.BOLD, size=15),
                                ft.Text(f"IP: {dev_ip}", size=12, color="grey"),
                            ], expand=True),
                            ft.ElevatedButton(
                                "Send",
                                icon=ft.Icons.SEND_ROUNDED,
                                on_click=lambda _: send_file_to(dev_ip)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                )
            )
            page.update()

    # Start mDNS Discovery
    disc = Discovery(my_name, on_device_found)
    disc.start()

    # UI Layout
    header = ft.Container(
        padding=15,
        border_radius=10,
        bgcolor="#22252a",
        content=ft.Column([
            ft.Text("Jhotpot Share", size=22, weight=ft.FontWeight.BOLD, color="blue"),
            ft.Row([
                ft.Icon(ft.Icons.COMPUTER, size=16, color="grey"),
                ft.Text(f"{my_name}", size=13, weight=ft.FontWeight.W_500),
            ]),
            ft.Row([
                ft.Icon(ft.Icons.WIFI, size=16, color="grey"),
                ft.Text(f"IP: {my_ip}", size=12, color="grey"),
            ])
        ])
    )

    page.add(
        header,
        ft.Divider(height=15, color="transparent"),

        ft.Text("Select file to share:", weight=ft.FontWeight.BOLD, size=14),
        ft.Row([
            ft.ElevatedButton(
                "Choose File",
                icon=ft.Icons.FOLDER_OPEN,
                on_click=open_native_file_picker
            ),
        ]),
        selected_file_text,

        ft.Divider(height=20),

        ft.Row([
            ft.Text("Nearby Discovered Devices:", weight=ft.FontWeight.BOLD, size=14),
            ft.ProgressRing(width=16, height=16, stroke_width=2)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

        ft.Container(content=device_list, expand=True)
    )


if __name__ == "__main__":
    ft.run(main)