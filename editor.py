import customtkinter as ctk
import json
from definitions import GridType, Rarity, ItemClass, Element, ItemType

# --- Constants for Editor UI ---
GRID_COLS, GRID_ROWS = 9, 7
GRID_COLORS = {-1: "#2B2B2B", 0:"#343638", 1:"#A9A9A9", 2:"#FFD700", 3:"#32CD32", 4:"#9400D3"}
BRUSH_NAMES = {-1: "NULL", 0: "EMPTY", 1: "BODY", 2: "STAR A", 3: "STAR B", 4: "STAR C"}

class ItemEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Backpack Battles - Item Editor")
        self.geometry("1400x800")
        ctk.set_appearance_mode("dark")
        
        self.items_data = self.load_json()
        self.current_item_key = None
        self.shape_matrix_data = [[-1 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.active_brush = -1

        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.input_frame = ctk.CTkFrame(self, corner_radius=10)
        self.input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.item_list_frame = ctk.CTkFrame(self, corner_radius=10)
        self.item_list_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        self.create_input_widgets()
        self.create_item_list_widgets()

    def load_json(self):
        try:
            with open('items.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def create_input_widgets(self):
        # --- Left Side: Input Form ---
        form_frame = ctk.CTkScrollableFrame(self.input_frame)
        form_frame.pack(expand=True, fill="both", padx=15, pady=15)

        # Name and Score
        ctk.CTkLabel(form_frame, text="Item Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ctk.CTkEntry(form_frame, width=250)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=2)
        
        ctk.CTkLabel(form_frame, text="Base Score:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.score_entry = ctk.CTkEntry(form_frame, width=100)
        self.score_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Dropdowns
        ctk.CTkLabel(form_frame, text="Rarity:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.rarity_var = ctk.StringVar(value=Rarity.COMMON.name)
        self.rarity_menu = ctk.CTkOptionMenu(form_frame, values=[r.name for r in Rarity], variable=self.rarity_var)
        self.rarity_menu.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(form_frame, text="Class:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.class_var = ctk.StringVar(value=ItemClass.NEUTRAL.name)
        self.class_menu = ctk.CTkOptionMenu(form_frame, values=[c.name for c in ItemClass], variable=self.class_var)
        self.class_menu.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Checkboxes for Multi-select
        self.element_vars = {}
        element_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        element_frame.grid(row=4, column=1, columnspan=2, padx=5, pady=10, sticky="w")
        ctk.CTkLabel(form_frame, text="Elements:").grid(row=4, column=0, padx=5, pady=10, sticky="w")
        for i, elem in enumerate(Element):
            var = ctk.StringVar(value="off")
            cb = ctk.CTkCheckBox(element_frame, text=elem.name, variable=var, onvalue="on", offvalue="off")
            cb.grid(row=i//4, column=i%4, padx=5, pady=2, sticky="w")
            self.element_vars[elem.name] = var

        self.type_vars = {}
        type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        type_frame.grid(row=5, column=1, columnspan=2, padx=5, pady=10, sticky="w")
        ctk.CTkLabel(form_frame, text="Types:").grid(row=5, column=0, padx=5, pady=10, sticky="w")
        for i, typ in enumerate(ItemType):
            var = ctk.StringVar(value="off")
            cb = ctk.CTkCheckBox(type_frame, text=typ.name, variable=var, onvalue="on", offvalue="off")
            cb.grid(row=i//4, column=i%4, padx=5, pady=2, sticky="w")
            self.type_vars[typ.name] = var

        # Reworked Shape Matrix Input
        shape_container = ctk.CTkFrame(form_frame, fg_color="transparent")
        shape_container.grid(row=6, column=1, padx=5, pady=10, sticky="w")
        ctk.CTkLabel(form_frame, text="Shape Matrix:").grid(row=6, column=0, padx=5, pady=10, sticky="nw")
        
        self.grid_frame = ctk.CTkFrame(shape_container)
        self.grid_frame.pack(side="left")
        self.grid_buttons = []
        for r in range(GRID_ROWS):
            row_btns = []
            for c in range(GRID_COLS):
                btn = ctk.CTkButton(self.grid_frame, text="", width=35, height=35, corner_radius=0, 
                                    fg_color=GRID_COLORS[-1], command=lambda r=r, c=c: self.paint_grid_cell(r,c))
                btn.grid(row=r, column=c, padx=1, pady=1)
                row_btns.append(btn)
            self.grid_buttons.append(row_btns)
        
        palette_frame = ctk.CTkFrame(shape_container, fg_color="transparent")
        palette_frame.pack(side="left", padx=20)
        self.palette_buttons = {}
        for val, name in BRUSH_NAMES.items():
            btn = ctk.CTkButton(palette_frame, text=name, command=lambda v=val: self.select_brush(v),
                                fg_color=GRID_COLORS[val])
            btn.pack(pady=3, fill="x")
            self.palette_buttons[val] = btn
            
        # Star Effects JSON Editor
        ctk.CTkLabel(form_frame, text="Star Effects (JSON):").grid(row=7, column=0, padx=5, pady=10, sticky="nw")
        self.star_effects_textbox = ctk.CTkTextbox(form_frame, height=200, width=500)
        self.star_effects_textbox.grid(row=7, column=1, columnspan=2, padx=5, pady=10, sticky="w")

        self.select_brush(-1)
        self.clear_fields()

    def create_item_list_widgets(self):
        ctk.CTkLabel(self.item_list_frame, text="Items", font=("", 18, "bold")).pack(pady=(10,5))
        self.list_scroll_frame = ctk.CTkScrollableFrame(self.item_list_frame)
        self.list_scroll_frame.pack(expand=True, fill="both", padx=10, pady=5)
        
        action_frame = ctk.CTkFrame(self.item_list_frame, fg_color="transparent")
        action_frame.pack(pady=10)

        self.save_button = ctk.CTkButton(action_frame, text="Save/Update Item", command=self.save_item)
        self.save_button.pack(pady=5, fill="x")
        self.delete_button = ctk.CTkButton(action_frame, text="Delete Loaded Item", fg_color="#D2691E", hover_color="#B85C1A", command=self.delete_item)
        self.delete_button.pack(pady=5, fill="x")
        self.clear_button = ctk.CTkButton(action_frame, text="Clear Form", fg_color="gray50", hover_color="gray30", command=self.clear_fields)
        self.clear_button.pack(pady=(15,5), fill="x")
        
        self.populate_item_list()

    def populate_item_list(self):
        for widget in self.list_scroll_frame.winfo_children(): widget.destroy()
        sorted_keys = sorted(self.items_data.keys(), key=lambda x: self.items_data.get(x, {}).get('name', ''))
        for item_key in sorted_keys:
            item_name = self.items_data[item_key]['name']
            btn = ctk.CTkButton(self.list_scroll_frame, text=item_name, command=lambda key=item_key: self.load_item_data(key), fg_color="gray25")
            btn.pack(pady=2, fill="x")

    def select_brush(self, brush_value):
        self.active_brush = brush_value
        for val, btn in self.palette_buttons.items():
            btn.configure(border_width=3 if val == brush_value else 1)

    def paint_grid_cell(self, r, c):
        self.shape_matrix_data[r][c] = self.active_brush
        self.grid_buttons[r][c].configure(fg_color=GRID_COLORS[self.active_brush])

    def load_item_data(self, item_key):
        self.clear_fields()
        self.current_item_key = item_key
        data = self.items_data[item_key]

        self.name_entry.insert(0, data.get("name", ""))
        self.score_entry.insert(0, str(data.get("base_score", 0)))
        self.rarity_var.set(data.get("rarity", Rarity.COMMON.name))
        self.class_var.set(data.get("item_class", ItemClass.NEUTRAL.name))

        for elem_name in data.get("elements", []):
            if elem_name in self.element_vars: self.element_vars[elem_name].set("on")
        for type_name in data.get("types", []):
            if type_name in self.type_vars: self.type_vars[type_name].set("on")
        
        star_effects = data.get("star_effects", {})
        self.star_effects_textbox.delete("1.0", "end")
        self.star_effects_textbox.insert("1.0", json.dumps(star_effects, indent=2))

        matrix = data.get("shape_matrix", [])
        h, w = len(matrix), len(matrix[0]) if matrix else 0
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                val = matrix[r][c] if r < h and c < w else -1
                self.shape_matrix_data[r][c] = val
                self.grid_buttons[r][c].configure(fg_color=GRID_COLORS[val])
    
    # --- RE-IMPLEMENTED CUSTOM SAVE FUNCTION ---
    def save_data_to_json(self, filepath, data):
        with open(filepath, 'w') as f:
            f.write("{\n")
            sorted_keys = sorted(data.keys())
            for i, item_key in enumerate(sorted_keys):
                item_data = data[item_key]
                f.write(f'  "{item_key}": {{\n')
                
                field_keys = list(item_data.keys())
                for j, field_key in enumerate(field_keys):
                    field_value = item_data[field_key]
                    f.write(f'    "{field_key}": ')
                    if field_key == "shape_matrix":
                        f.write("[\n")
                        for k, row in enumerate(field_value):
                            row_str = str(row).replace(" ", "")
                            f.write(f'      {row_str}')
                            if k < len(field_value) - 1: f.write(',')
                            f.write('\n')
                        f.write('    ]')
                    elif isinstance(field_value, dict):
                         f.write(json.dumps(field_value, indent=4).replace('\n', '\n    '))
                    else:
                        f.write(json.dumps(field_value))
                    
                    if j < len(field_keys) - 1: f.write(',')
                    f.write('\n')
                
                f.write('  }')
                if i < len(sorted_keys) - 1: f.write(',')
                f.write('\n')
            f.write("}\n")

    def save_item(self):
        item_name = self.name_entry.get()
        if not item_name:
            print("Item Name cannot be empty!")
            return

        min_r, max_r, min_c, max_c = GRID_ROWS, -1, GRID_COLS, -1
        has_content = any(self.shape_matrix_data[r][c] != -1 for r in range(GRID_ROWS) for c in range(GRID_COLS))
        if has_content:
            for r in range(GRID_ROWS):
                for c in range(GRID_COLS):
                    if self.shape_matrix_data[r][c] != -1:
                        min_r, max_r, min_c, max_c = min(min_r,r), max(max_r,r), min(min_c,c), max(max_c,c)
            
            trimmed_matrix = [[self.shape_matrix_data[r][c] if self.shape_matrix_data[r][c] != -1 else 0 
                               for c in range(min_c, max_c + 1)] 
                              for r in range(min_r, max_r + 1)]
        else:
            trimmed_matrix = []

        try:
            star_effects_text = self.star_effects_textbox.get("1.0", "end").strip()
            star_effects_data = json.loads(star_effects_text or "{}")
        except json.JSONDecodeError:
            print("ERROR: Invalid JSON in Star Effects. Please correct it and save again.")
            return

        item_key = item_name.replace(" ", "")
        
        new_data = {
            "name": item_name,
            "rarity": self.rarity_var.get(),
            "item_class": self.class_var.get(),
            "elements": sorted([name for name, var in self.element_vars.items() if var.get() == "on"]),
            "types": sorted([name for name, var in self.type_vars.items() if var.get() == "on"]),
            "base_score": int(self.score_entry.get() or 0),
            "shape_matrix": trimmed_matrix,
            "star_effects": star_effects_data
        }
        self.items_data[item_key] = new_data
        
        self.save_data_to_json('items.json', self.items_data)
        
        print(f"Saved '{item_name}' successfully!")
        self.populate_item_list()
        self.clear_fields()

    def delete_item(self):
        if self.current_item_key and self.current_item_key in self.items_data:
            item_name_to_delete = self.items_data[self.current_item_key]['name']
            del self.items_data[self.current_item_key]
            self.save_data_to_json('items.json', self.items_data)
            print(f"Deleted '{item_name_to_delete}' successfully!")
            self.populate_item_list()
            self.clear_fields()
        else:
            print("No item loaded to delete.")
            
    def clear_fields(self):
        self.name_entry.delete(0, 'end')
        self.score_entry.delete(0, 'end')
        self.rarity_var.set(Rarity.COMMON.name)
        self.class_var.set(ItemClass.NEUTRAL.name)
        for var in self.element_vars.values(): var.set("off")
        for var in self.type_vars.values(): var.set("off")
        self.star_effects_textbox.delete("1.0", "end")
        self.star_effects_textbox.insert("1.0", "{\n  \n}")
        
        self.shape_matrix_data = [[-1 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                self.grid_buttons[r][c].configure(fg_color=GRID_COLORS[-1])
        self.current_item_key = None
        self.select_brush(-1)

if __name__ == "__main__":
    app = ItemEditorApp()
    app.mainloop()

