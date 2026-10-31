"""
========================================================================
 Miami Campus - Student Network Client (برنامج الزبون / العميل)
 Architecture: Client-Server Model (نظام خادم - زبون)
 Strict Specialty Isolation (كل طالب يرى تخصصـه فقط)
========================================================================
"""

import sys
import argparse
import json
import urllib.request
import urllib.error
import urllib.parse

DEFAULT_SERVER = "http://127.0.0.1:5000"

class MiamiCampusClient:
    def __init__(self, server_url=DEFAULT_SERVER):
        self.server_url = server_url.rstrip('/')
        self.current_user = None

    def _request(self, endpoint, method="GET", data=None):
        url = f"{self.server_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.current_user:
            headers["X-Student-Id"] = str(self.current_user["id"])

        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                resp_text = response.read().decode("utf-8")
                return json.loads(resp_text)
        except urllib.error.HTTPError as e:
            err_text = e.read().decode("utf-8")
            try:
                return json.loads(err_text)
            except Exception:
                return {"success": False, "error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_server(self):
        print(f"\n[*] Connecting to Miami Campus Server at {self.server_url}...")
        res = self._request("/api/status")
        if res.get("status") == "online":
            print(f" [✓] Connected to       : {res.get('server')}")
            print(f" [✓] Architecture       : {res.get('architecture')}")
            print(f" [✓] Channel Isolation  : {res.get('specialty_isolation')}")
            print(f" [✓] Verified Students  : {res.get('total_students')}")
            print(f" [✓] Total Discussions  : {res.get('total_discussions')}")
            return True
        else:
            print(f" [✗] Failed to connect: {res.get('error')}")
            return False

    def register(self, full_name, email, specialty, country, password, bio=""):
        data = {
            "full_name": full_name,
            "email": email,
            "specialty": specialty,
            "country": country,
            "password": password,
            "bio": bio
        }
        res = self._request("/api/register", method="POST", data=data)
        if res.get("success"):
            print(f"\n[✓] Registration Successful! Welcome {full_name} to Miami Campus.")
            print(f"[✓] Assigned to private channel: {specialty}")
            self.current_user = res.get("student")
            return True
        else:
            print(f"\n[✗] Registration Failed: {res.get('error')}")
            return False

    def login(self, email, password):
        data = {"email": email, "password": password}
        res = self._request("/api/login", method="POST", data=data)
        if res.get("success"):
            self.current_user = res.get("student")
            print(f"\n[✓] Signed in as: {self.current_user['full_name']}")
            print(f"[✓] Active Specialty Channel: {self.current_user['specialty']} (Country: {self.current_user['country']})")
            return True
        else:
            print(f"\n[✗] Sign-in Failed: {res.get('error')}")
            return False

    def list_discussions(self, country=None):
        if not self.current_user:
            print("\n[!] Please sign in first (Option 4) to view your department discussions.")
            return []

        endpoint = "/api/discussions"
        if country:
            endpoint += f"?country={urllib.parse.quote(country)}"

        res = self._request(endpoint)
        if res.get("success"):
            posts = res.get("discussions", [])
            channel = res.get("specialty_channel", self.current_user["specialty"])
            print(f"\n=== Department Channel: {channel} ({len(posts)} Discussions) ===")
            if not posts:
                print("    (No discussions yet in your department. Use option 5 to post one!)")
            for p in posts:
                author = p["author"]
                print(f"\n#{p['id']} {p['title']}")
                print(f"    By: {author['full_name']} 🏛️ {author['country']}")
                print(f"    Date: {p['created_at'][:16]} | Likes: {p['like_count']} | Replies: {p['comment_count']}")
                print(f"    Preview: {p['content'][:120]}...")
            return posts
        else:
            print(f"[✗] Error: {res.get('error')}")
            return []

    def post_discussion(self, title, content):
        if not self.current_user:
            print("\n[!] Please sign in first to publish discussions.")
            return False
        data = {
            "title": title,
            "content": content
        }
        res = self._request("/api/discussions", method="POST", data=data)
        if res.get("success"):
            print(f"\n[✓] Discussion successfully published to {res.get('specialty')}! (ID: {res.get('post_id')})")
            return True
        else:
            print(f"\n[✗] Failed to publish discussion: {res.get('error')}")
            return False

def interactive_client(server_url):
    client = MiamiCampusClient(server_url)
    if not client.check_server():
        print(f"\nMake sure the central server is running (python server.py) and reachable at {server_url}.")
        return

    while True:
        if client.current_user:
            user_info = f"{client.current_user['full_name']} 🏛️ Channel: [{client.current_user['specialty']}]"
        else:
            user_info = "Guest (Not signed in)"

        print("\n" + "=" * 60)
        print(" 🏛️  MIAMI CAMPUS - STUDENT CLIENT CONSOLE (واجهة الزبون)")
        print(f" Current Status: {user_info}")
        print("=" * 60)
        print(" 1. View My Department Discussions (عرض مناقشات تخصصي فقط)")
        print(" 2. Filter My Department by Classmate Country (تصفية حسب الدولة)")
        print(" 3. Register New Student Account (تسجيل حساب طالب جديد)")
        print(" 4. Campus Sign In (تسجيل الدخول)")
        print(" 5. Publish Discussion to My Department (نشر مناقشة في تخصصي)")
        print(" 6. Check Server Connection Status (فحص حالة الخادم)")
        print(" 7. Exit Client (خروج)")
        print("-" * 60)

        choice = input("Select an option (1-7): ").strip()

        if choice == '1':
            client.list_discussions()
        elif choice == '2':
            if not client.current_user:
                print("\n[!] Please sign in first (Option 4).")
                continue
            country = input("Enter classmate country (e.g. Algeria, France, United States): ").strip()
            client.list_discussions(country=country)
        elif choice == '3':
            print("\n--- Register Student Account ---")
            name = input("Full Name: ").strip()
            spec = input("Specialty / Major: ").strip()
            country = input("Country: ").strip()
            email = input("Miami Email (@student.miami.edu): ").strip()
            pwd = input("Password (min 6 chars): ").strip()
            bio = input("Bio (optional): ").strip()
            client.register(name, email, spec, country, pwd, bio)
        elif choice == '4':
            print("\n--- Campus Sign In ---")
            email = input("University Email: ").strip()
            pwd = input("Password: ").strip()
            client.login(email, pwd)
        elif choice == '5':
            if not client.current_user:
                print("\n[!] Please sign in first (Option 4) to post.")
                continue
            print(f"\n--- Publishing into: {client.current_user['specialty']} ---")
            title = input("Discussion Title: ").strip()
            content = input("Discussion Content: ").strip()
            client.post_discussion(title, content)
        elif choice == '6':
            client.check_server()
        elif choice == '7':
            print("Exiting Miami Campus Client. Goodbye!")
            break
        else:
            print("Invalid option. Please choose 1-7.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Miami Campus Network Client (برنامج الزبون)")
    parser.add_argument('--server', default=DEFAULT_SERVER, help="Miami Campus Server URL (e.g. http://192.168.1.12:5000)")
    args = parser.parse_args()

    interactive_client(args.server)
