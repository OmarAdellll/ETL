import customtkinter as ctk
from app.etl.autoComplete.ai_complete import (AIAutocompletePopup,AIAutocompleteEngine) 
from typing import Optional

class SQLGeneratorDialog(ctk.CTkToplevel):
    """Enhanced SQL Generator Dialog with AI Autocomplete"""
    
    def __init__(self, master, title="Generate SQL with AI", 
                 text="Describe what data you want (natural language):"):
        super().__init__(master)
        self.title(title)
        self.geometry("500x400")
        self.resizable(False, False)
        
        self.user_input = None
        self.autocomplete_engine = AIAutocompleteEngine()
        self.popup: Optional[AIAutocompletePopup] = None

        # Instructions label
        instructions = (
            "💡 Try phrases like:\n"
            "• I want Land Surface Temperature for Suez, Egypt...\n"
            "• Show me NDVI data for Cairo from Jan 2022 to Dec 2022\n"
            "• Give me precipitation in Alexandria at 30m scale"
        )
        self.instructions_label = ctk.CTkLabel(
            self, text=instructions, font=("Roboto", 10), 
            text_color="#808080", anchor="w", justify="left"
        )
        self.instructions_label.pack(pady=10, padx=20, anchor="w")

        self.label = ctk.CTkLabel(self, text=text, font=("Roboto", 14))
        self.label.pack(pady=5, padx=20, anchor="w")

        # Textbox with larger font
        self.textbox = ctk.CTkTextbox(self, height=180, font=("Consolas", 12))
        self.textbox.pack(pady=5, padx=20, fill="both", expand=True)
        
        # Bind events for autocomplete
        self.textbox.bind('<KeyRelease>', self._on_key_release)
        self.textbox.bind('<Control-space>', self._on_ctrl_space)
        self.textbox.bind('<Escape>', self._on_escape)
        self.textbox.bind('<Up>', self._on_up)
        self.textbox.bind('<Down>', self._on_down)
        self.textbox.bind('<Return>', self._on_return)
        self.textbox.bind('<Tab>', self._on_tab)

        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=20, padx=20, fill="x")

        self.generate_btn = ctk.CTkButton(
            self.button_frame, text="Generate SQL", 
            command=self.on_generate, width=120,
            fg_color="#51ab46", hover_color="#387731"
        )
        self.generate_btn.pack(side="right", padx=5)

        self.cancel_btn = ctk.CTkButton(
            self.button_frame, text="Cancel", 
            command=self.on_cancel, width=80
        )
        self.cancel_btn.pack(side="right", padx=5)
        
        # Make modal
        self.transient(master)
        self.grab_set()
        self.textbox.focus_set()
    
    def _on_key_release(self, event):
        """Handle key release for autocomplete"""
        if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Return', 'Escape', 'Tab']:
            return
        
        if event.char and len(event.char) == 1:
            self._show_autocomplete()
    
    def _on_ctrl_space(self, event):
        """Ctrl+Space triggers autocomplete"""
        self._show_autocomplete()
        return "break"
    
    def _on_escape(self, event):
        """Escape closes popup"""
        if self.popup:
            self.popup.destroy()
            self.popup = None
            return "break"
    
    def _on_up(self, event):
        """Up arrow"""
        if self.popup:
            self.popup.move_selection_up()
            return "break"
    
    def _on_down(self, event):
        """Down arrow"""
        if self.popup:
            self.popup.move_selection_down()
            return "break"
    
    def _on_return(self, event):
        """Return key"""
        if self.popup:
            self.popup.select_current()
            return "break"
    
    def _on_tab(self, event):
        """Tab key"""
        if self.popup:
            self.popup.select_current()
            return "break"
    
    def _show_autocomplete(self):
        """Show autocomplete popup"""
        if self.popup:
            self.popup.destroy()
            self.popup = None
        
        # Get cursor position
        cursor_index = self.textbox.index("insert")
        row, col = map(int, cursor_index.split('.'))
        
        # Get text
        all_text = self.textbox.get("1.0", "end-1c")
        cursor_pos = self._get_position_from_index(all_text, row - 1, col)
        
        # Get suggestions
        suggestions = self.autocomplete_engine.get_suggestions(all_text, cursor_pos)
        
        if not suggestions:
            return
        
        # Calculate popup position
        bbox = self.textbox.bbox(f"{row}.{col}")
        if bbox:
            x = self.textbox.winfo_rootx() + bbox[0]
            y = self.textbox.winfo_rooty() + bbox[1] + bbox[3]
            
            self.popup = AIAutocompletePopup(
                self.textbox, suggestions, self._insert_suggestion, x, y
            )
    
    def _insert_suggestion(self, text: str):
        """Insert suggestion"""
        cursor_index = self.textbox.index("insert")
        row, col = map(int, cursor_index.split('.'))
        
        # Get current line
        line_start = f"{row}.0"
        line_end = f"{row}.end"
        line_text = self.textbox.get(line_start, line_end)
        
        # Find word start
        word_start = col
        while word_start > 0 and line_text[word_start - 1] not in ' \t\n':
            word_start -= 1
        
        # Delete partial word
        delete_start = f"{row}.{word_start}"
        self.textbox.delete(delete_start, cursor_index)
        
        # Insert suggestion
        self.textbox.insert(delete_start, text)
        
        # Add space
        new_col = word_start + len(text)
        self.textbox.insert(f"{row}.{new_col}", " ")
        self.textbox.mark_set("insert", f"{row}.{new_col + 1}")
        
        if self.popup:
            self.popup.destroy()
            self.popup = None
    
    def _get_position_from_index(self, text: str, row: int, col: int) -> int:
        """Convert row/col to position"""
        lines = text.split('\n')
        position = 0
        
        for i in range(row):
            if i < len(lines):
                position += len(lines[i]) + 1
        
        position += col
        return position

    def on_generate(self):
        self.user_input = self.textbox.get("1.0", "end-1c").strip()
        self.destroy()

    def on_cancel(self):
        self.destroy()

    def get_input(self):
        self.wait_window()
        return self.user_input