import customtkinter as ctk

class SQLGeneratorDialog(ctk.CTkToplevel):
    def __init__(self, master, title="Generate SQL", text="Enter your request:"):
        super().__init__(master)
        self.title(title)
        self.geometry("400x300")
        self.resizable(False, False)
        
        self.user_input = None

        self.label = ctk.CTkLabel(self, text=text, font=("Roboto", 14))
        self.label.pack(pady=10, padx=20, anchor="w")

        self.textbox = ctk.CTkTextbox(self, height=150)
        self.textbox.pack(pady=5, padx=20, fill="x")

        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=20, padx=20, fill="x")

        self.generate_btn = ctk.CTkButton(self.button_frame, text="Generate", command=self.on_generate)
        self.generate_btn.pack(side="right", padx=5)

        self.cancel_btn = ctk.CTkButton(self.button_frame, text="Cancel", command=self.on_cancel, border_width=1)
        self.cancel_btn.pack(side="right", padx=5)
        
        # Make modal
        self.transient(master)
        self.grab_set()
        self.focus_set()

    def on_generate(self):
        self.user_input = self.textbox.get("1.0", "end-1c").strip()
        self.destroy()

    def on_cancel(self):
        self.destroy()

    def get_input(self):
        self.wait_window()
        return self.user_input