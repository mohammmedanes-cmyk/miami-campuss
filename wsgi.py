from app import app, start_server

# Initialize database on startup
start_server()

if __name__ == "__main__":
    app.run()
