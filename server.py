"""
========================================================================
 Miami Campus - Central Network Server (خادم الشبكة المركزي)
 Architecture: Client-Server Model (نظام خادم - زبون)
========================================================================
This server listens on 0.0.0.0, allowing any client device (laptops,
smartphones, or desktop client apps) on the university local network (LAN / Wi-Fi)
to connect, register, and participate in private campus discussions.
"""

import sys
import socket
import os
import io

def get_network_ip():
    """Finds the local LAN IP address of this machine on the university network."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def print_terminal_qr(url):
    """Prints a scannable ASCII QR Code directly in the terminal for phone cameras."""
    try:
        import qrcode
        # Ensure utf-8 encoding for Unicode block characters
        if sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        print("\n 📱 SCAN THIS QR CODE WITH YOUR PHONE CAMERA TO CONNECT IMMEDIATELY:")
        print(" (امسح رمز الاستجابة السريعة بكاميرا الهاتف للاتصال فوراً)")
        print("-" * 55)
        qr.print_ascii(invert=True)
        print("-" * 55)
    except Exception as e:
        pass

def run_central_server(host='0.0.0.0', port=5000):
    from app import app, start_server
    start_server()
    lan_ip = get_network_ip()
    network_url = f"http://{lan_ip}:{port}"

    print("=" * 70)
    print(" 🏛️  MIAMI CAMPUS - CENTRAL NETWORK SERVER (خادم الشبكة المركزي)")
    print("    Architecture: Client-Server Model (نظام خادم - زبون)")
    print("    Strict Specialty Isolation (كل طالب يرى تخصصـه فقط)")
    print("=" * 70)
    print(f" [✓] Server Status       : ONLINE & LISTENING on all interfaces (0.0.0.0)")
    print(f" [✓] Localhost Access    : http://127.0.0.1:{port}")
    print(f" [✓] Phone & Network URL : {network_url}")
    print(f" [✓] REST API Base URL   : {network_url}/api")
    print(f" [✓] Instant QR Image    : {network_url}/qr.png")
    print("-" * 70)

    # Print ASCII QR code in the terminal
    print_terminal_qr(network_url)

    print(" 🌐 HOW STUDENTS & CLIENTS CONNECT FROM THEIR PHONES:")
    print(f" 1. Connect phone to the SAME Wi-Fi or hotspot as this computer.")
    print(f" 2. Point phone camera at the QR code above OR open browser to: {network_url}")
    print(f" 3. Register or sign in to enter your specialty discussion channel.")
    print("=" * 70)
    print(" Server is actively running. Press Ctrl+C to stop.\n")

    try:
        from waitress import serve
        print(f" [*] Running multi-threaded production WSGI server (Waitress) on {host}:{port}...")
        serve(app, host=host, port=port, threads=8)
    except ImportError:
        print(f" [*] Running Flask server on {host}:{port}...")
        app.run(host=host, port=port, threaded=True, debug=False)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    run_central_server(port=port)
