import socket
import threading
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser, ServiceListener


def get_my_ip():
    """ডিভাইসের Local IP বের করার ফাংশন"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


class Discovery:
    def __init__(self, name, on_found):
        self.name = name
        self.on_found = on_found
        self.zc = None

    def _run_discovery(self):
        """আলাদা ব্যাকগ্রাউন্ড থ্রেডে Zeroconf চালানো যাতে Flet EventLoop ব্লক না হয়"""
        try:
            self.zc = Zeroconf()
            ip = get_my_ip()
            type_ = "_handshare._tcp.local."
            service_name = f"{self.name.replace(' ', '_')}.{type_}"

            info = ServiceInfo(
                type_,
                service_name,
                addresses=[socket.inet_aton(ip)],
                port=5000,
                properties={'name': self.name.encode('utf-8')}
            )
            self.zc.register_service(info)

            outer_self = self

            class Listener(ServiceListener):
                def add_service(self, zc, type_, name):
                    info = zc.get_service_info(type_, name)
                    if info and info.addresses:
                        dev_ip = socket.inet_ntoa(info.addresses[0])
                        raw_name = info.properties.get(b'name', b'Unknown Device')
                        dev_name = raw_name.decode('utf-8') if isinstance(raw_name, bytes) else str(raw_name)

                        if dev_ip != get_my_ip():
                            outer_self.on_found(dev_name, dev_ip)

                def remove_service(self, zc, type_, name):
                    pass

                def update_service(self, zc, type_, name):
                    pass

            ServiceBrowser(self.zc, type_, Listener())
        except Exception as e:
            print(f"Discovery error: {e}")

    def start(self):
        # ব্যাকগ্রাউন্ড থ্রেডে স্টার্ট করা হলো
        threading.Thread(target=self._run_discovery, daemon=True).start()

    def stop(self):
        if self.zc:
            try:
                self.zc.close()
            except Exception:
                pass