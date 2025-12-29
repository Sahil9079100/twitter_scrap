# customtkinter window here and this will be main window
import customtkinter as ctk
import json
import threading
from typing import Optional

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # "dark", "light", or "system"
ctk.set_default_color_theme("blue")  # "blue", "green", or "dark-blue"

# --- Global logging utility ---
import os
LOG_FILE = "scraper_logs.txt"

# Clear log file on start
with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("")

def log_to_terminal(text: str, color: str = "#ffffff") -> None:
    """Write log to file with color code separator."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            # Format: COLOR|TEXT
            f.write(f"{color}|{text}\n")
    except Exception as e:
        print(f"Log error: {e}")
    
    # Fallback print
    print(text)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Start log watcher
        self.last_log_pos = 0
        self.after(100, self._check_logs)
        
        # Window configuration
        self.title("Twitter Scraper")
        self.configure(fg_color="#1a1a1a")  # Dark gray background
        
        # Center window on screen
        self.window_width = 900
        self.window_height = 600
        self._center_window()
        
        # Build UI
        self._create_widgets()
    
    def _center_window(self):
        """Center the window on screen."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
    
    def _create_widgets(self):
        """Create all UI widgets."""
        self._create_heading()
        self._create_tagline()
        self._create_primary_button()
    
    def _create_heading(self):
        """Create the main heading."""
        self.heading = ctk.CTkLabel(
            self,
            text="X Profile Scraper",
            font=("Consolas", 36, "bold"),
            text_color="#00FF04"
        )
        self.heading.pack(pady=(30, 5))
    
    def _create_tagline(self):
        """Create the tagline below heading."""
        self.tagline = ctk.CTkLabel(
            self,
            text="Scrape profile tweets easily — fully automated",
            font=("Consolas", 14),
            text_color="#888888"
        )
        self.tagline.pack(pady=(0, 20))
    
    def _create_primary_button(self):
        """Create the primary action button."""
        self.primary_btn = ctk.CTkButton(
            self,
            text="INITIALIZE",
            font=("Consolas", 16, "bold"),
            width=200,
            height=45,
            corner_radius=0,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            text_color="#ffffff",
            border_width=2,
            border_color="#5a5a5a",
            command=self._on_initialize_click
        )
        self.primary_btn.pack(pady=30)
    
    def _on_initialize_click(self):
        """Handle primary button click - transition to main page."""
        # Clear current widgets
        self.heading.destroy()
        self.tagline.destroy()
        self.primary_btn.destroy()
        
        # Show main page
        self._create_main_page()
    
    def _create_main_page(self):
        """Create the main scraper page after initialization."""
        
        # --- Row 1: Profile Name ---
        self.profile_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.profile_frame.pack(pady=(50, 20))
        
        self.input_label = ctk.CTkLabel(
            self.profile_frame,
            text="Enter profile name:",
            font=("Consolas", 16),
            text_color="#888888"
        )
        self.input_label.pack(side="left", padx=(0, 15))
        
        self.username_entry = ctk.CTkEntry(
            self.profile_frame,
            placeholder_text="elonmusk",
            font=("Consolas", 14),
            width=500,
            height=40,
            corner_radius=0,
            fg_color="#2a2a2a",
            border_color="#5a5a5a",
            border_width=2,
            text_color="#ffffff",
            placeholder_text_color="#666666"
        )
        self.username_entry.pack(side="left")
        
        # --- Row 2: Limit + Start From ---
        self.options_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.options_frame.pack(pady=(0, 20))
        
        # Limit
        self.limit_label = ctk.CTkLabel(
            self.options_frame,
        # text="Enter profile name:",
            text="      Limit:       ",
            font=("Consolas", 16),
            text_color="#888888"
        )
        self.limit_label.pack(side="left", padx=(0, 15))
        self._create_tooltip(self.limit_label, "A Limit is how many tweets to fetch,\nkeeping it empty will fetch all the tweets of that profile")
        
        self.limit_entry = ctk.CTkEntry(
            self.options_frame,
            placeholder_text="ex: 50",
            font=("Consolas", 14),
            width=500,
            height=40,
            corner_radius=0,
            fg_color="#2a2a2a",
            border_color="#5a5a5a",
            border_width=2,
            text_color="#ffffff",
            placeholder_text_color="#666666"
        )
        self.limit_entry.pack(side="left")
        
        # Start From
        # self.start_label = ctk.CTkLabel(
        #     self.options_frame,
        #     text="Start From:",
        #     font=("Consolas", 16),
        #     text_color="#888888"
        # )
        # self.start_label.pack(side="left", padx=(0, 10))
        # self._create_tooltip(self.start_label, "Put the initial tweet number to fetch tweets from\nthat specific point, if you have to fetch tweet\nfrom the 56th tweet then type 56")
        
        # self.start_entry = ctk.CTkEntry(
        #     self.options_frame,
        #     placeholder_text="ex: 100",
        #     font=("Consolas", 14),
        #     width=240,
        #     height=40,
        #     corner_radius=0,
        #     fg_color="#2a2a2a",
        #     border_color="#5a5a5a",
        #     border_width=2,
        #     text_color="#ffffff",
        #     placeholder_text_color="#666666"
        # )
        # self.start_entry.pack(side="left")
        
        # --- Row 3: Output File Type ---
        # self.output_frame = ctk.CTkFrame(self, fg_color="transparent")
        # self.output_frame.pack(pady=10)
        
        # self.output_label = ctk.CTkLabel(
        #     self.output_frame,
        #     text="Output file type:",
        #     font=("Consolas", 16),
        #     text_color="#888888"
        # )
        # self.output_label.pack(side="left", padx=(0, 20))
        
        # Radio button variable
        # self.output_type_var = ctk.StringVar(value=".csv")
        
        # self.csv_radio = ctk.CTkRadioButton(
        #     self.output_frame,
        #     text=".csv",
        #     font=("Consolas", 14),
        #     variable=self.output_type_var,
        #     value=".csv",
        #     fg_color="#00FF04",
        #     border_color="#5a5a5a",
        #     hover_color="#00CC03",
        #     text_color="#ffffff"
        # )
        # self.csv_radio.pack(side="left", padx=(0, 30))
        
        # self.json_radio = ctk.CTkRadioButton(
        #     self.output_frame,
        #     text=".json",
        #     font=("Consolas", 14),
        #     variable=self.output_type_var,
        #     value=".json",
        #     fg_color="#00FF04",
        #     border_color="#5a5a5a",
        #     hover_color="#00CC03",
        #     text_color="#ffffff"
        # )
        # self.json_radio.pack(side="left")
        
        # --- Row 3: Login Credentials ---
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.login_frame.pack(pady=(0, 20))

        # My Username
        self.my_user_label = ctk.CTkLabel(
            self.login_frame,
            text="Your Username:",
            font=("Consolas", 16),
            text_color="#888888"
        )
        self.my_user_label.pack(side="left", padx=(0, 15))
        
        self.my_user_entry = ctk.CTkEntry(
            self.login_frame,
            placeholder_text="my_handle",
            font=("Consolas", 14),
            width=200,
            height=40,
            corner_radius=0,
            fg_color="#2a2a2a",
            border_color="#5a5a5a",
            border_width=2,
            text_color="#ffffff",
            placeholder_text_color="#666666"
        )
        self.my_user_entry.pack(side="left", padx=(0, 20))

        # My Password
        self.my_pass_label = ctk.CTkLabel(
            self.login_frame,
            text="Your Password:",
            font=("Consolas", 16),
            text_color="#888888"
        )
        self.my_pass_label.pack(side="left", padx=(0, 15))
        
        self.my_pass_entry = ctk.CTkEntry(
            self.login_frame,
            placeholder_text="password",
            show="*",
            font=("Consolas", 14),
            width=200,
            height=40,
            corner_radius=0,
            fg_color="#2a2a2a",
            border_color="#5a5a5a",
            border_width=2,
            text_color="#ffffff",
            placeholder_text_color="#666666"
        )
        self.my_pass_entry.pack(side="left")
        
        # --- Next Button ---
        self.next_btn = ctk.CTkButton(
            self,
            text="START SCRAPING",
            font=("Consolas", 16, "bold"),
            width=200,
            height=45,
            corner_radius=0,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            text_color="#ffffff",
            border_width=2,
            border_color="#5a5a5a",
            command=self._on_start_click
        )
        self.next_btn.pack(pady=30)

        # --- Terminal (fills remaining space) ---
        self._create_terminal()
    
    def _on_start_click(self):
        """Handle START SCRAPING button click."""
        _username = None
        _limit = None
        _my_user = None
        _my_pass = None

        # Validate Target Username
        if self.username_entry.get() == "":
            self.username_entry.insert(0, "Please enter a username")
            self.after(2000, lambda: self.username_entry.delete(0, 'end'))
            return
        elif self.username_entry.get() == "Please enter a username":
            return
        else:
            _username = self.username_entry.get()

        # Validate Limit
        if self.limit_entry.get() == "":
            _limit = "100000000"
        else:
            _limit = self.limit_entry.get()

        # Validate Login Credentials
        if self.my_user_entry.get() == "":
            self.my_user_entry.insert(0, "Required")
            self.after(2000, lambda: self.my_user_entry.delete(0, 'end'))
            return
        else:
            _my_user = self.my_user_entry.get()

        if self.my_pass_entry.get() == "":
            self.my_pass_entry.insert(0, "Required")
            self.after(2000, lambda: self.my_pass_entry.delete(0, 'end'))
            return
        else:
            _my_pass = self.my_pass_entry.get()
        
        data = {
            "username": _username,
            "limit": _limit,
            "my_username": _my_user,
            "my_password": _my_pass
        }
        
        # Save config
        log_to_terminal("Configuration saved.", "#31E934")
        try:
            with open('data.config.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            log_to_terminal(f"Error saving config: {e}", "#FF4444")
            return
        
        # Start Automation Thread
        log_to_terminal("Initializing automation...", "#00FF04")
        self.next_btn.configure(state="disabled", text="RUNNING...")
        
        def run_scraper():
            try:
                import twitter_login_scrape as scraper
                # Reload config in module to pick up new file
                scraper.load_config()
                scraper.run_automator()
            except Exception as e:
                log_to_terminal(f"Scraper error: {e}", "#FF4444")
            finally:
                self.after(0, lambda: self.next_btn.configure(
                    state="normal",
                    text="START SCRAPING",
                    command=self._on_start_click
                ))
        
        thread = threading.Thread(target=run_scraper, daemon=True)
        thread.start()

    def _create_tooltip(self, widget, text):
        """Create a tooltip balloon for a widget."""
        tooltip = None
        
        def show_tooltip(event):
            nonlocal tooltip
            x = widget.winfo_rootx() + widget.winfo_width() // 2
            y = widget.winfo_rooty() - 10
            
            tooltip = ctk.CTkToplevel(self)
            tooltip.wm_overrideredirect(True)
            tooltip.configure(fg_color="#3a3a3a")
            
            label = ctk.CTkLabel(
                tooltip,
                text=text,
                font=("Consolas", 12),
                text_color="#ffffff",
                fg_color="#3a3a3a",
                corner_radius=0,
                padx=10,
                pady=5
            )
            label.pack()
            
            tooltip.update_idletasks()
            tooltip_width = tooltip.winfo_width()
            tooltip_height = tooltip.winfo_height()
            tooltip.wm_geometry(f"+{x - tooltip_width // 2}+{y - tooltip_height}")
        
        def hide_tooltip(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    # --- Terminal creation & logging ---
    def _create_terminal(self):
        """Create a read-only scrollable terminal-like textbox."""
        self.terminal = ctk.CTkTextbox(
            self,
            fg_color="#000000",   # pitch black background
            corner_radius=0,
            width=self.window_width,
        )
        self.terminal.configure(font=("Consolas", 12))
        self.terminal.configure(state="disabled")  # read-only
        self.terminal.pack(fill="both", expand=True)

        # Prime with a welcome line
        self.append_log("Terminal initialized.")

    def append_log(self, text: str, color: str = "#ffffff") -> None:
        """Append a colored line to the terminal and scroll to bottom."""
        # Enable editing
        self.terminal.configure(state="normal")

        # Create a tag per color if not existing
        tag_name = f"color_{color}"
        try:
            # Attempt to get current tag config; if raises, we'll create it
            self.terminal.tag_cget(tag_name, "foreground")
        except Exception:
            self.terminal.tag_config(tag_name, foreground=color)

        # Insert text with color tag and newline
        self.terminal.insert("end", text + "\n", tag_name)
        self.terminal.see("end")  # scroll to bottom

        # Disable editing again
        self.terminal.configure(state="disabled")

    def _check_logs(self):
        """Poll log file for new entries."""
        # Wait until terminal is initialized
        if not hasattr(self, 'terminal'):
            self.after(100, self._check_logs)
            return

        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    f.seek(self.last_log_pos)
                    new_lines = f.readlines()
                    self.last_log_pos = f.tell()
                
                for line in new_lines:
                    if "|" in line:
                        parts = line.strip().split("|", 1)
                        if len(parts) == 2:
                            color, text = parts
                            self.append_log(text, color)
        except Exception:
            pass
        
        # Check again in 100ms
        self.after(100, self._check_logs)


if __name__ == "__main__":
    app = App()
    app.mainloop()