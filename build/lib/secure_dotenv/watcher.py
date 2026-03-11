import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import os

class EnvFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".env"):
            print(f"🚨 Detected accidental .env creation at {event.src_path}")
            print("⚠️ Please run 'secure-dotenv migrate' to secure it.")
            # In Phase 2: Auto-trigger the migration logic here.

def start_watcher():
    path = str(Path.cwd())
    event_handler = EnvFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print(f"👁️ secure_dotenv daemon is watching {path} for plain-text leaks...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()