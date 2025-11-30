"""
GUI Wrapper for Zelun Scheduler

This is a simple GUI wrapper that calls the YouTube upload script.
"""

import os
import subprocess
import sys
import json
import tkinter as tk
import threading
import queue
from pathlib import Path
from tkinter import scrolledtext, ttk, messagebox

SCRIPT_DIR = Path(__file__).parent.resolve()
YOUTUBE_SCRIPT = SCRIPT_DIR / "youtube_bulk_scheduler.py"
GUI_SETTINGS_FILE = SCRIPT_DIR / "gui_settings.json"


class BulkSchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Zelun Scheduler")
        self.root.geometry("1000x750")
        
        # Variables
        self.dry_run_var = tk.BooleanVar()
        self.start_date_var = tk.StringVar()
        self.timezone_var = tk.StringVar(value="America/Sao_Paulo")
        self.hour_slots_var = tk.StringVar(value="8 18")
        self.category_id_var = tk.StringVar(value="20")
        self.description_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        
        # Threading and process control
        self.process = None
        self.process_thread = None
        self.output_queue = queue.Queue()
        self.is_running = False
        
        # Load saved settings
        self.load_settings()
        
        self.setup_ui()
        
        # Save settings when window closes
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Zelun Scheduler", font=("Arial", 16, "bold"))
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
        
        # Description
        ttk.Label(config_frame, text="Description:").grid(row=4, column=0, sticky=tk.W, pady=2)
        description_entry = scrolledtext.ScrolledText(config_frame, height=3, width=40)
        description_entry.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        # Load saved description if available
        saved_description = self.description_var.get()
        if saved_description:
            description_entry.insert(1.0, saved_description)
        description_entry.bind('<KeyRelease>', lambda e: self.description_var.set(description_entry.get(1.0, tk.END).strip()))
        self.description_entry = description_entry
        
        # Tags
        ttk.Label(config_frame, text="Tags:").grid(row=5, column=0, sticky=tk.W, pady=2)
        tags_entry = ttk.Entry(config_frame, textvariable=self.tags_var, width=40)
        tags_entry.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(config_frame, text="(comma-separated)").grid(row=5, column=3, sticky=tk.W, padx=5)
        
        # Dry run checkbox
        ttk.Checkbutton(config_frame, text="Dry Run (Preview Only)", variable=self.dry_run_var).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Configure column weights for resizing
        config_frame.columnconfigure(1, weight=1)
        
        # Upload button
        upload_frame = ttk.LabelFrame(main_frame, text="Upload", padding="10")
        upload_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.youtube_button = ttk.Button(
            upload_frame, 
            text="📺 Upload to YouTube", 
            command=lambda: self.run_scheduler(),
            width=30
        )
        self.youtube_button.pack(pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_process, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Open Clips Folder", command=self.open_clips_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="View History", command=self.view_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="View Logs", command=self.view_logs).pack(side=tk.LEFT, padx=5)
        
        # Output area
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, width=80)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
    def run_scheduler(self):
        """Run the YouTube scheduler script with current settings (asynchronously)."""
        if self.is_running:
            messagebox.showwarning("Warning", "Process is already running!")
            return
        
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "Starting YouTube Scheduler...\n\n")
        
        # Disable upload button and enable stop button
        self.youtube_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_running = True
        
        # Build command
        cmd = self._build_command()
        
        # Save settings before running
        self.save_settings()
        
        # Start the process in a separate thread
        self.process_thread = threading.Thread(target=self._run_process_thread, args=(cmd,), daemon=True)
        self.process_thread.start()
        
        # Start checking for output
        self.check_output()
    
    def _build_command(self) -> list:
        """Build command for YouTube upload."""
        cmd = [sys.executable, str(YOUTUBE_SCRIPT)]
        
        if self.start_date_var.get():
            cmd.extend(["--start-date", self.start_date_var.get()])
        
        if self.timezone_var.get():
            cmd.extend(["--timezone", self.timezone_var.get()])
        
        if self.hour_slots_var.get():
            hours = self.hour_slots_var.get().split()
            cmd.extend(["--hour-slots"] + hours)
        
        if self.category_id_var.get():
            cmd.extend(["--category-id", self.category_id_var.get()])
        
        # Add description if provided
        description = self.description_entry.get(1.0, tk.END).strip()
        if description:
            description_escaped = description.replace('"', '""')
            cmd.extend(["--description", description_escaped])
        
        # Add tags if provided
        tags = self.tags_var.get().strip()
        if tags:
            cmd.extend(["--tags", tags])
        
        if self.dry_run_var.get():
            cmd.append("--dry-run")
        
        return cmd
    
    def _run_process_thread(self, cmd):
        """Run the subprocess in a separate thread and queue output."""
        try:
            # Run script and capture output
            # Use UTF-8 encoding explicitly to handle emojis and special characters
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid characters instead of failing
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output to queue
            for line in self.process.stdout:
                if not self.is_running:  # Check if process was stopped
                    break
                self.output_queue.put(line)
            
            # Wait for process to complete
            return_code = self.process.wait()
            self.output_queue.put(('RETURN_CODE', return_code))
            
        except Exception as e:
            error_msg = f"Error running script: {e}"
            self.output_queue.put(('ERROR', error_msg))
    
    def check_output(self):
        """Check for output from the process thread and update GUI."""
        try:
            while True:
                try:
                    item = self.output_queue.get_nowait()
                    
                    if isinstance(item, tuple):
                        if item[0] == 'RETURN_CODE':
                            return_code = item[1]
                            if return_code == 0:
                                self.output_text.insert(tk.END, "\n\n✅ Process completed successfully!\n")
                                messagebox.showinfo("Success", "Upload process completed successfully!")
                            else:
                                self.output_text.insert(tk.END, f"\n\n❌ Process exited with code {return_code}\n")
                                messagebox.showerror("Error", f"Process exited with code {return_code}")
                            self._reset_buttons()
                            return
                        elif item[0] == 'ERROR':
                            error_msg = item[1]
                            self.output_text.insert(tk.END, f"\n\n❌ {error_msg}\n")
                            messagebox.showerror("Error", error_msg)
                            self._reset_buttons()
                            return
                    else:
                        # Regular output line
                        self.output_text.insert(tk.END, item)
                        self.output_text.see(tk.END)
                        
                except queue.Empty:
                    break
        except Exception as e:
            error_msg = f"Error processing output: {e}"
            self.output_text.insert(tk.END, f"\n\n❌ {error_msg}\n")
            self._reset_buttons()
            return
        
        # Schedule next check
        if self.is_running:
            self.root.after(100, self.check_output)  # Check every 100ms
    
    def stop_process(self):
        """Stop the running process."""
        if not self.is_running or self.process is None:
            return
        
        self.is_running = False
        try:
            if self.process:
                self.process.terminate()
                # Wait a bit, then kill if still running
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
        except Exception as e:
            self.output_text.insert(tk.END, f"\n\n⚠️ Error stopping process: {e}\n")
        
        self.output_text.insert(tk.END, "\n\n⚠️ Process stopped by user.\n")
        self._reset_buttons()
    
    def _reset_buttons(self):
        """Reset button states after process completes."""
        self.is_running = False
        self.youtube_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.process = None
    
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
        history_file = SCRIPT_DIR / "logs" / "upload_history.json"
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
        log_file = SCRIPT_DIR / "logs" / "error_log.txt"
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
    
    def load_settings(self):
        """Load saved GUI settings from file."""
        if GUI_SETTINGS_FILE.exists():
            try:
                with open(GUI_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Load all settings except start_date
                    self.description_var.set(settings.get('description', ''))
                    self.tags_var.set(settings.get('tags', ''))
                    self.timezone_var.set(settings.get('timezone', 'America/Sao_Paulo'))
                    self.hour_slots_var.set(settings.get('hour_slots', '8 18'))
                    self.category_id_var.set(settings.get('category_id', '20'))
                    self.dry_run_var.set(settings.get('dry_run', False))
            except Exception as e:
                # If loading fails, use defaults
                pass
    
    def save_settings(self):
        """Save GUI settings to file (except start_date)."""
        try:
            # Get description from entry widget
            description = self.description_entry.get(1.0, tk.END).strip() if hasattr(self, 'description_entry') else self.description_var.get()
            settings = {
                'description': description,
                'tags': self.tags_var.get(),
                'timezone': self.timezone_var.get(),
                'hour_slots': self.hour_slots_var.get(),
                'category_id': self.category_id_var.get(),
                'dry_run': self.dry_run_var.get()
                # Note: start_date is intentionally not saved
            }
            with open(GUI_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Silently fail - not critical
            pass
    
    def on_closing(self):
        """Handle window closing event."""
        if self.is_running:
            self.stop_process()
            # Wait a moment for process to stop
            if self.process_thread and self.process_thread.is_alive():
                self.process_thread.join(timeout=2)
        
        self.save_settings()
        self.root.destroy()


def main():
    """Launch the GUI application."""
    root = tk.Tk()
    app = BulkSchedulerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
