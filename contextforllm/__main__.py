import os
import sys
import subprocess
import webbrowser
import time

def main():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(app_dir, "app.py")

    print("")
    print("Starting ContextForLLM...")
    print("")

    process = subprocess.Popen(
        [sys.executable, app_path],
        cwd=app_dir
    )

    time.sleep(2)
    webbrowser.open("http://127.0.0.1:5000")

    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        print("")
        print("ContextForLLM stopped.")
        print("")

if __name__ == "__main__":
    main()

    