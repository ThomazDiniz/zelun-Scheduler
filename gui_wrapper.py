"""
GUI Wrapper for YouTube Bulk Scheduler

This is a simple GUI wrapper that calls the main script.
The main script (youtube_bulk_scheduler.py) is NOT modified.
"""

import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext, ttk, messagebox, filedialog

SCRIPT_DIR = Path(__file__).parent.resolve()
MAIN_SCRIPT = SCRIPT_DIR / "youtube_bulk_scheduler.py"


class YouTubeSchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Bulk Scheduler")
        self.root.geometry("800x600")
        
        # Variables
        self.dry_run_var = tk.BooleanVar()
        self.start_date_var = tk.StringVar()
        self.timezone_var = tk.StringVar(value="America/Sao_Paulo")
        self.hour_slots_var = tk.StringVar(value="8 18")
        self.category_id_var = tk.StringVar(value="20")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="YouTube Bulk Video Scheduler", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Configuration section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Start date
        ttk.Label(config_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(config_frame, textvariable=self.start_date_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Label(config_frame, text="(Leave empty for today)").grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # Timezone
        ttk.Label(config_frame, text="Timezone:").grid(row=1, column=0, sticky=tk.W, pady=2)
        timezone_combo = ttk.Combobox(config_frame, textvariable=self.timezone_var, width=20)
        timezone_combo['values'] = ("America/Sao_Paulo", "America/New_York", "America/Los_Angeles", "Europe/London", "Asia/Tokyo")
        timezone_combo.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Hour slots
        ttk.Label(config_frame, text="Hour Slots:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(config_frame, textvariable=self.hour_slots_var, width=20).grid(row=2, column=1, sticky=tk.W, pady=2)
        ttk.Label(config_frame, text="(e.g., '8 18' for 8am and 6pm)").grid(row=2, column=2, sticky=tk.W, padx=5)
        
        # Category ID
        ttk.Label(config_frame, text="Category ID:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(config_frame, textvariable=self.category_id_var, width=20).grid(row=3, column=1, sticky=tk.W, pady=2)
        ttk.Label(config_frame, text="(20 = Gaming)").grid(row=3, column=2, sticky=tk.W, padx=5)
        
        # Dry run checkbox
        ttk.Checkbutton(config_frame, text="Dry Run (Preview Only)", variable=self.dry_run_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Run Scheduler", command=self.run_scheduler).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Open Clips Folder", command=self.open_clips_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="View History", command=self.view_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="View Logs", command=self.view_logs).pack(side=tk.LEFT, padx=5)
        
        # Output area
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, width=80)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
    def run_scheduler(self):
        """Run the scheduler script with current settings."""
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "Starting YouTube Scheduler...\n\n")
        self.root.update()
        
        # Build command
        cmd = [sys.executable, str(MAIN_SCRIPT)]
        
        if self.start_date_var.get():
            cmd.extend(["--start-date", self.start_date_var.get()])
        
        if self.timezone_var.get():
            cmd.extend(["--timezone", self.timezone_var.get()])
        
        if self.hour_slots_var.get():
            hours = self.hour_slots_var.get().split()
            cmd.extend(["--hour-slots"] + hours)
        
        if self.category_id_var.get():
            cmd.extend(["--category-id", self.category_id_var.get()])
        
        if self.dry_run_var.get():
            cmd.append("--dry-run")
        
        try:
            # Run script and capture output
            # Use UTF-8 encoding explicitly to handle emojis and special characters
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid characters instead of failing
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output to text widget
            for line in process.stdout:
                self.output_text.insert(tk.END, line)
                self.output_text.see(tk.END)
                self.root.update()
            
            process.wait()
            
            if process.returncode == 0:
                self.output_text.insert(tk.END, "\n\n✅ Process completed successfully!\n")
                messagebox.showinfo("Success", "Upload process completed successfully!")
            else:
                self.output_text.insert(tk.END, f"\n\n❌ Process exited with code {process.returncode}\n")
                messagebox.showerror("Error", f"Process exited with code {process.returncode}")
                
        except Exception as e:
            error_msg = f"Error running script: {e}"
            self.output_text.insert(tk.END, f"\n\n❌ {error_msg}\n")
            messagebox.showerror("Error", error_msg)
    
    def open_clips_folder(self):
        """Open the clips folder in file explorer."""
        clips_folder = SCRIPT_DIR / "clips"
        clips_folder.mkdir(exist_ok=True)
        
        if sys.platform == "win32":
            os.startfile(str(clips_folder))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(clips_folder)])
        else:
            subprocess.run(["xdg-open", str(clips_folder)])
    
    def view_history(self):
        """Open upload history in a new window."""
        history_file = SCRIPT_DIR / "upload_history.json"
        if not history_file.exists():
            messagebox.showinfo("Info", "No upload history found yet.")
            return
        
        history_window = tk.Toplevel(self.root)
        history_window.title("Upload History")
        history_window.geometry("600x400")
        
        text_widget = scrolledtext.ScrolledText(history_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        try:
            import json
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                text_widget.insert(1.0, json.dumps(history, indent=2))
        except Exception as e:
            text_widget.insert(1.0, f"Error reading history: {e}")
    
    def view_logs(self):
        """Open error log in a new window."""
        log_file = SCRIPT_DIR / "error_log.txt"
        if not log_file.exists():
            messagebox.showinfo("Info", "No error log found yet.")
            return
        
        log_window = tk.Toplevel(self.root)
        log_window.title("Error Log")
        log_window.geometry("600x400")
        
        text_widget = scrolledtext.ScrolledText(log_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                text_widget.insert(1.0, f.read())
        except Exception as e:
            text_widget.insert(1.0, f"Error reading log: {e}")


def main():
    """Launch the GUI application."""
    root = tk.Tk()
    app = YouTubeSchedulerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

