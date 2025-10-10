import customtkinter as ctk
import json
from tkinter import filedialog
from definitions import GridType, Rarity, ItemClass, Element, ItemType, EFFECT_TYPES, CONDITION_TYPES

# --- Constants for Editor UI ---
GRID_COLS, GRID_ROWS = 9, 7
GRID_COLORS = {-1: "#2B2B2B", 0:"#343638", 1:"#A9A9A9", 2:"#FFD700", 3:"#32CD32", 4:"#9400D3"}
BRUSH_NAMES = {-1: "NULL", 0: "EMPTY", 1: "BODY", 2: "STAR A", 3: "STAR B", 4: "STAR C"}
STAR_EFFECT_KEYS = ["STAR_A_1", "STAR_A_2", "STAR_B_1", "STAR_B_2", "STAR_C_1", "STAR_C_2"]
LOGIC_OPTIONS = ["Match All (AND)", "Match Any (OR)"]

class ItemEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Backpack Battles - Advanced Item Editor")
        self.geometry("1400x900")
        ctk.set_appearance_mode("dark")
        
        self.items_data = self.load_json()
        self.current_item_key = None
        self.shape_matrix_data = [[-1 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.active_brush = -1
        self.effect_widgets = {}

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
            with open('items.json', 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return {}

    def create_input_widgets(self):
        form_frame = ctk.CTkScrollableFrame(self.input_frame)
        form_frame.pack(expand=True, fill="both", padx=15, pady=15)

        ctk.CTkLabel(form_frame, text="Item Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ctk.CTkEntry(form_frame, width=250)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=3)
        
        ctk.CTkLabel(form_frame, text="Base Score:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.score_entry = ctk.CTkEntry(form_frame, width=100)
        self.score_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.cooldown_var = ctk.StringVar(value="off")
        self.cooldown_checkbox = ctk.CTkCheckBox(form_frame, text="Has Cooldown", variable=self.cooldown_var, onvalue="on", offvalue="off")
        self.cooldown_checkbox.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        
        self.start_of_battle_var = ctk.StringVar(value="off")
        self.start_of_battle_checkbox = ctk.CTkCheckBox(form_frame, text="Start of Battle", variable=self.start_of_battle_var, onvalue="on", offvalue="off")
        self.start_of_battle_checkbox.grid(row=1, column=3, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(form_frame, text="Rarity:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.rarity_var = ctk.StringVar(value=Rarity.COMMON.name)
        self.rarity_menu = ctk.CTkOptionMenu(form_frame, values=[r.name for r in Rarity], variable=self.rarity_var)
        self.rarity_menu.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(form_frame, text="Class:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.class_var = ctk.StringVar(value=ItemClass.NEUTRAL.name)
        self.class_menu = ctk.CTkOptionMenu(form_frame, values=[c.name for c in ItemClass], variable=self.class_var)
        self.class_menu.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        self.element_vars, self.type_vars = {}, {}
        ctk.CTkLabel(form_frame, text="Elements:").grid(row=4, column=0, padx=5, pady=10, sticky="w")
        element_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        element_frame.grid(row=4, column=1, columnspan=3, padx=5, pady=10, sticky="w")
        for i, elem in enumerate(Element):
            var = ctk.StringVar(value="off"); cb = ctk.CTkCheckBox(element_frame, text=elem.name, variable=var, onvalue="on", offvalue="off")
            cb.grid(row=i//4, column=i%4, padx=5, pady=2, sticky="w"); self.element_vars[elem.name] = var

        ctk.CTkLabel(form_frame, text="Types:").grid(row=5, column=0, padx=5, pady=10, sticky="w")
        type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        type_frame.grid(row=5, column=1, columnspan=3, padx=5, pady=10, sticky="w")
        for i, typ in enumerate(ItemType):
            var = ctk.StringVar(value="off"); cb = ctk.CTkCheckBox(type_frame, text=typ.name, variable=var, onvalue="on", offvalue="off")
            cb.grid(row=i//4, column=i%4, padx=5, pady=2, sticky="w"); self.type_vars[typ.name] = var
        
        ctk.CTkLabel(form_frame, text="Shape Matrix:").grid(row=6, column=0, padx=5, pady=10, sticky="nw")
        shape_container = ctk.CTkFrame(form_frame, fg_color="transparent"); shape_container.grid(row=6, column=1, columnspan=3, padx=5, pady=10, sticky="w")
        self.grid_frame = ctk.CTkFrame(shape_container); self.grid_frame.pack(side="left"); self.grid_buttons = []
        for r in range(GRID_ROWS):
            row_btns = []
            for c in range(GRID_COLS):
                btn = ctk.CTkButton(self.grid_frame, text="", width=35, height=35, corner_radius=0, fg_color=GRID_COLORS[-1], command=lambda r=r, c=c: self.paint_grid_cell(r,c))
                btn.grid(row=r, column=c, padx=1, pady=1); row_btns.append(btn)
            self.grid_buttons.append(row_btns)
        palette_frame = ctk.CTkFrame(shape_container, fg_color="transparent"); palette_frame.pack(side="left", padx=20); self.palette_buttons = {}
        for val, name in BRUSH_NAMES.items():
            btn = ctk.CTkButton(palette_frame, text=name, command=lambda v=val: self.select_brush(v), fg_color=GRID_COLORS[val])
            btn.pack(pady=3, fill="x"); self.palette_buttons[val] = btn

        ctk.CTkLabel(form_frame, text="Effects:").grid(row=7, column=0, padx=5, pady=10, sticky="nw")
        self.effect_tab_view = ctk.CTkTabview(form_frame, width=700); self.effect_tab_view.grid(row=7, column=1, columnspan=3, padx=5, pady=10, sticky="w")
        self.effect_tab_view.add("Star Effects"); self.effect_tab_view.add("Passive Effects")
        
        self.star_effect_tab_view = ctk.CTkTabview(self.effect_tab_view.tab("Star Effects")); self.star_effect_tab_view.pack(expand=True, fill="both")
        for star_key in STAR_EFFECT_KEYS: self.star_effect_tab_view.add(star_key)
        
        for star_key in STAR_EFFECT_KEYS: self._create_effect_ui(self.star_effect_tab_view.tab(star_key), star_key)
        self._create_effect_ui(self.effect_tab_view.tab("Passive Effects"), "passive_effects")

        self.select_brush(-1)
        self.clear_fields()

    def _create_effect_ui(self, parent, key):
        self.effect_widgets[key] = {'scroll_frame': None, 'effects': []}
        scroll_frame = ctk.CTkScrollableFrame(parent, label_text=f"Effects List for {key}")
        scroll_frame.pack(expand=True, fill="both", padx=5, pady=5)
        self.effect_widgets[key]['scroll_frame'] = scroll_frame
        ctk.CTkButton(parent, text="+ Add Effect", command=lambda p=scroll_frame, k=key: self._add_effect_frame(p, k)).pack(pady=5, padx=5, side="bottom")

    def _add_effect_frame(self, parent, key, effect_data=None):
        effect_frame = ctk.CTkFrame(parent, border_width=1)
        effect_frame.pack(pady=5, padx=5, fill="x", expand=True)
        
        effect_frame.grid_columnconfigure(1, weight=1)
        
        control_frame = ctk.CTkFrame(effect_frame, fg_color="transparent")
        control_frame.grid(row=0, column=2, padx=5, pady=5, sticky="ne")
        ctk.CTkButton(control_frame, text="↑", width=25, command=lambda f=effect_frame, p=parent: self._move_effect(p, f, "up")).pack(side="left")
        ctk.CTkButton(control_frame, text="↓", width=25, command=lambda f=effect_frame, p=parent: self._move_effect(p, f, "down")).pack(side="left", padx=2)
        ctk.CTkButton(control_frame, text="X", width=25, command=lambda f=effect_frame: self._remove_effect_frame(f, key)).pack(side="left")
        
        ctk.CTkLabel(effect_frame, text="Effect Type:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        effect_type_var = ctk.StringVar(value=effect_data.get('effect', EFFECT_TYPES[0]) if effect_data else EFFECT_TYPES[0])
        ctk.CTkOptionMenu(effect_frame, variable=effect_type_var, values=EFFECT_TYPES).grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        ctk.CTkLabel(effect_frame, text="Value:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        value_entry = ctk.CTkEntry(effect_frame)
        value_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        if effect_data and 'value' in effect_data: value_entry.insert(0, str(effect_data['value']))

        # --- NEW: Condition Logic Dropdown ---
        ctk.CTkLabel(effect_frame, text="Condition Logic:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        logic_var = ctk.StringVar(value=LOGIC_OPTIONS[0])
        if effect_data and effect_data.get("condition_logic", "AND") == "OR":
            logic_var.set(LOGIC_OPTIONS[1])
        ctk.CTkOptionMenu(effect_frame, variable=logic_var, values=LOGIC_OPTIONS).grid(row=2, column=1, padx=5, pady=2, sticky="w")

        conditions_frame = ctk.CTkFrame(effect_frame, fg_color="transparent")
        conditions_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(conditions_frame, text="Conditions:").pack(anchor="w")
        ctk.CTkButton(conditions_frame, text="+ Add Condition", height=20, command=lambda p=conditions_frame: self._add_condition_row(p)).pack(anchor="w", pady=2)
        
        effect_frame.widgets = {'effect_type': effect_type_var, 'value': value_entry, 'logic': logic_var, 'conditions': []}
        if effect_data and "condition" in effect_data:
            for k, v in effect_data["condition"].items():
                self._add_condition_row(conditions_frame, {"type": k, "value": v})
        
        self.effect_widgets[key]['effects'].append(effect_frame)

    def _remove_effect_frame(self, frame_to_remove, key):
        if frame_to_remove in self.effect_widgets[key]['effects']:
            self.effect_widgets[key]['effects'].remove(frame_to_remove)
        frame_to_remove.destroy()

    def _move_effect(self, parent, frame_to_move, direction):
        children = list(parent.pack_slaves())
        if frame_to_move not in children: return

        current_index = children.index(frame_to_move)
        new_index = current_index + (-1 if direction == "up" else 1)
        
        if 0 <= new_index < len(children):
            children.pop(current_index)
            children.insert(new_index, frame_to_move)
            for child in parent.pack_slaves(): child.pack_forget()
            for child in children: child.pack(pady=5, padx=5, fill="x", expand=True)

    def _add_condition_row(self, parent, condition_data=None):
        condition_row = ctk.CTkFrame(parent)
        condition_row.pack(fill="x", pady=2)
        
        cond_type_var = ctk.StringVar(value=condition_data.get("type", CONDITION_TYPES[0]) if condition_data else CONDITION_TYPES[0])
        ctk.CTkOptionMenu(condition_row, variable=cond_type_var, values=CONDITION_TYPES).pack(side="left", padx=5)
        
        cond_value_entry = ctk.CTkEntry(condition_row)
        cond_value_entry.pack(side="left", padx=5, expand=True, fill="x")
        if condition_data and "value" in condition_data: cond_value_entry.insert(0, str(condition_data["value"]))
        
        ctk.CTkButton(condition_row, text="x", width=25, command=condition_row.destroy).pack(side="right", padx=5)
        
        parent.master.widgets['conditions'].append({'type': cond_type_var, 'value': cond_value_entry, 'frame': condition_row})

    def create_item_list_widgets(self):
        ctk.CTkLabel(self.item_list_frame, text="Items", font=("", 18, "bold")).pack(pady=(10,5))
        self.list_scroll_frame = ctk.CTkScrollableFrame(self.item_list_frame)
        self.list_scroll_frame.pack(expand=True, fill="both", padx=10, pady=5)
        
        action_frame = ctk.CTkFrame(self.item_list_frame, fg_color="transparent")
        action_frame.pack(pady=10)
        ctk.CTkButton(action_frame, text="Save/Update Item", command=self.save_item).pack(pady=5, fill="x")
        ctk.CTkButton(action_frame, text="Delete Loaded Item", fg_color="#D2691E", hover_color="#B85C1A", command=self.delete_item).pack(pady=5, fill="x")
        
        io_frame = ctk.CTkFrame(action_frame)
        io_frame.pack(pady=(15,5), fill="x")
        ctk.CTkButton(io_frame, text="Import from JSON...", command=self.import_json).pack(pady=(0,5), fill="x")
        ctk.CTkButton(io_frame, text="Export to JSON...", command=self.export_json).pack(pady=0, fill="x")
        
        ctk.CTkButton(action_frame, text="Clear Form", fg_color="gray50", hover_color="gray30", command=self.clear_fields).pack(pady=5, fill="x")
        self.populate_item_list()

    def import_json(self):
        filepath = filedialog.askopenfilename(title="Import Item JSON", filetypes=(("JSON files", "*.json"), ("All files", "*.*")))
        if not filepath: return
        try:
            with open(filepath, 'r') as f: self.items_data = json.load(f)
            print(f"Successfully imported items from {filepath}")
            self.populate_item_list()
            self.clear_fields()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error importing file: {e}")

    def export_json(self):
        filepath = filedialog.asksaveasfilename(title="Export Items to JSON", defaultextension=".json", filetypes=(("JSON files", "*.json"), ("All files", "*.*")))
        if not filepath: return
        try:
            with open(filepath, 'w') as f: json.dump(self.items_data, f, indent=2)
            print(f"Successfully exported current items to {filepath}")
        except Exception as e:
            print(f"Error exporting file: {e}")

    def populate_item_list(self):
        for widget in self.list_scroll_frame.winfo_children(): widget.destroy()
        sorted_keys = sorted(self.items_data.keys(), key=lambda x: self.items_data.get(x, {}).get('name', ''))
        for item_key in sorted_keys:
            btn = ctk.CTkButton(self.list_scroll_frame, text=self.items_data[item_key]['name'], command=lambda k=item_key: self.load_item_data(k), fg_color="gray25")
            btn.pack(pady=2, fill="x")

    def select_brush(self, brush_value):
        self.active_brush = brush_value
        for val, btn in self.palette_buttons.items(): btn.configure(border_width=3 if val == brush_value else 1)

    def paint_grid_cell(self, r, c):
        self.shape_matrix_data[r][c] = self.active_brush
        self.grid_buttons[r][c].configure(fg_color=GRID_COLORS[self.active_brush])

    def load_item_data(self, item_key):
        self.clear_fields(); self.current_item_key = item_key; data = self.items_data[item_key]
        self.name_entry.insert(0, data.get("name", "")); self.score_entry.insert(0, str(data.get("base_score", 0)))
        self.rarity_var.set(data.get("rarity", Rarity.COMMON.name)); self.class_var.set(data.get("item_class", ItemClass.NEUTRAL.name))
        if data.get("has_cooldown", False): self.cooldown_var.set("on")
        if data.get("is_start_of_battle", False): self.start_of_battle_var.set("on")
        for name in data.get("elements", []): self.element_vars[name].set("on")
        for name in data.get("types", []): self.type_vars[name].set("on")
        
        for effect in data.get("passive_effects", []): self._add_effect_frame(self.effect_widgets["passive_effects"]['scroll_frame'], "passive_effects", effect)
        
        for star_key, effects in data.get("star_effects", {}).items():
            if star_key in self.effect_widgets:
                if isinstance(effects, dict): effects = [effects]
                for effect in effects: 
                    self._add_effect_frame(self.effect_widgets[star_key]['scroll_frame'], star_key, effect)

        matrix = data.get("shape_matrix", []); h = len(matrix); w = len(matrix[0]) if h > 0 else 0
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                val = matrix[r][c] if r < h and c < w else -1
                self.shape_matrix_data[r][c] = val
                self.grid_buttons[r][c].configure(fg_color=GRID_COLORS[val])

    def save_item(self):
        item_name = self.name_entry.get()
        if not item_name: return
        item_key = item_name.replace(" ", "")

        min_r,max_r,min_c,max_c=GRID_ROWS,-1,GRID_COLS,-1; has_content = False
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.shape_matrix_data[r][c] != -1: has_content=True; min_r=min(min_r,r); max_r=max(max_r,r); min_c=min(min_c,c); max_c=max(max_c,c)
        trimmed_matrix = [[self.shape_matrix_data[r][c] if self.shape_matrix_data[r][c]!=-1 else 0 for c in range(min_c, max_c+1)] for r in range(min_r, max_r+1)] if has_content else []

        new_data = {
            "name": item_name, "rarity": self.rarity_var.get(), "item_class": self.class_var.get(),
            "elements": sorted([name for name, var in self.element_vars.items() if var.get() == "on"]),
            "types": sorted([name for name, var in self.type_vars.items() if var.get() == "on"]),
            "base_score": int(self.score_entry.get() or 0), "has_cooldown": self.cooldown_var.get() == "on",
            "is_start_of_battle": self.start_of_battle_var.get() == "on",
            "shape_matrix": trimmed_matrix, "passive_effects": [], "star_effects": {}
        }

        all_effect_keys = STAR_EFFECT_KEYS + ["passive_effects"]
        for key in all_effect_keys:
            effect_list = []
            scroll_frame = self.effect_widgets[key]['scroll_frame']
            for w in scroll_frame.pack_slaves():
                if isinstance(w, ctk.CTkFrame) and hasattr(w, 'widgets'):
                    value_str = w.widgets['value'].get()
                    try: value = eval(value_str)
                    except (NameError, SyntaxError): value = value_str
                    
                    logic_str = "AND" if w.widgets['logic'].get() == LOGIC_OPTIONS[0] else "OR"
                    effect_data = {"effect": w.widgets['effect_type'].get(), "value": value, "condition_logic": logic_str, "condition": {}}
                    
                    for cond in w.widgets['conditions']:
                        if cond['frame'].winfo_exists():
                            cond_type = cond['type'].get(); cond_val_str = cond['value'].get()
                            try: cond_val = eval(cond_val_str)
                            except (NameError, SyntaxError): cond_val = cond_val_str
                            effect_data["condition"][cond_type] = cond_val
                    effect_list.append(effect_data)

            if key == "passive_effects":
                if effect_list: new_data["passive_effects"] = effect_list
            else:
                if effect_list: new_data["star_effects"][key] = effect_list
        
        self.items_data[item_key] = new_data
        with open('items.json', 'w') as f: json.dump(self.items_data, f, indent=2)
        print(f"Saved '{item_name}' successfully!")
        self.populate_item_list(); self.clear_fields()

    def delete_item(self):
        if self.current_item_key and self.current_item_key in self.items_data:
            item_name = self.items_data[self.current_item_key]['name']
            del self.items_data[self.current_item_key]
            with open('items.json', 'w') as f: json.dump(self.items_data, f, indent=2)
            print(f"Deleted '{item_name}' successfully!")
            self.populate_item_list(); self.clear_fields()

    def clear_fields(self):
        self.name_entry.delete(0, 'end'); self.score_entry.delete(0, 'end')
        self.rarity_var.set(Rarity.COMMON.name); self.class_var.set(ItemClass.NEUTRAL.name)
        for var in self.element_vars.values(): var.set("off")
        for var in self.type_vars.values(): var.set("off")
        self.cooldown_var.set("off")
        self.start_of_battle_var.set("off")
        
        for key in self.effect_widgets:
            scroll_frame = self.effect_widgets[key]['scroll_frame']
            if scroll_frame:
                for widget in scroll_frame.winfo_children():
                    widget.destroy()
        
        self.shape_matrix_data = [[-1 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS): self.grid_buttons[r][c].configure(fg_color=GRID_COLORS[-1])
        self.current_item_key = None; self.select_brush(-1)

if __name__ == "__main__":
    app = ItemEditorApp()
    app.mainloop()