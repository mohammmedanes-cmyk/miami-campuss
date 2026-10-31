# Miami Campus 🏛️
> Private University Student Discussion Platform based on the **Client-Server Architecture** (نظام شبكة خادم - عميل / زبون) in **Crimson Red & Navy Blue**.

---

## 🌐 Client-Server Network Architecture (نظام خادم - زبون)

```
        ┌────────────────────────────────────────────────────────┐
        │       MIAMI CAMPUS CENTRAL SERVER (الخادم المركزي)     │
        │           Runs on: 0.0.0.0:5000 (Waitress WSGI)        │
        │           Database: university_forum.db (SQLite)       │
        └───────────────────────────┬────────────────────────────┘
                                    │
               Local Wi-Fi / University LAN Network
             ┌──────────────────────┼──────────────────────┐
             ▼                      ▼                      ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │  CLIENT 1 (زبون) │    │  CLIENT 2 (زبون) │    │  CLIENT 3 (زبون) │
    │ Laptop / Browser│    │ Phone / Mobile  │    │ Python CLI App  │
    │ 192.168.1.X     │    │ 192.168.1.Y     │    │ client.py       │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

1. **Central Server (`server.py`) - الخادم المركزي**:
   - Listens on `0.0.0.0:5000` across all network interfaces (Ethernet, Wi-Fi).
   - High-concurrency multi-threaded server (`Waitress` WSGI) handling concurrent student requests.
   - Automatically detects and displays the machine's local IP address (e.g. `http://192.168.1.12:5000`).
   - Private database holding registered students, discussions, comments, and upvotes.
   - Built-in REST API (`/api/...`) for programmatic client access.

2. **Client Applications (الزبائن / العملاء)**:
   - **Web Browser Client**: Any student on the university network visits `http://<SERVER_IP>:5000` on their laptop or phone.
   - **Dedicated Client Console (`client.py`)**: A standalone client program connecting over HTTP sockets to register, sign in, read discussions, and publish new posts.

---

## 🚀 How to Run the Client-Server System

### 1. Start the Central Server (الخادم)
On the server computer, run:
```powershell
python server.py
```
*(Or double-click `start_server.bat`)*

The server will print its network address:
```
[✓] Local Client URL    : http://127.0.0.1:5000
[✓] Network Client URL  : http://192.168.1.12:5000
```

### 2. Connect from Client Devices (الزبائن)
- **From any student phone or laptop on the university Wi-Fi**:
  Open the browser and enter:
  `http://192.168.1.12:5000`

- **Or from the dedicated Client application (`client.py`)**:
  ```powershell
  python client.py --server http://192.168.1.12:5000
  ```
  *(Or double-click `start_client.bat`)*

---

## 🔒 Private Campus Registration

Every student creating an account must provide:
1. **Full Name** (الاسم الكامل)
2. **Specialty / Academic Major** (التخصص الدراسي)
3. **Country** (الدولة)
4. **Official University Email** (`@student.miami.edu` or `@miami.edu`)
5. **Password** (min 6 characters)

---

## 👥 Pre-seeded Student Demo Accounts

| Student Name | Email | Specialty / Major | Country | Password |
|---|---|---|---|---|
| **Sarah Mansouri** | `sarah.m@student.miami.edu` | Computer Science & IT | Algeria | `password123` |
| **Lucas Dubois** | `lucas.d@student.miami.edu` | Medicine & Healthcare | France | `password123` |
| **Marcus Vance** | `marcus.v@student.miami.edu` | Mechanical Engineering | United States | `password123` |
| **Amina El-Sayed** | `amina.e@student.miami.edu` | Business Administration | Egypt | `password123` |
| **Elena Weber** | `elena.w@student.miami.edu` | Law & International Relations | Germany | `password123` |
