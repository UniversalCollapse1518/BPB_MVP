# -*- coding: utf-8 -*-
import customtkinter as ctk
import json
import os
from tkinter import filedialog, messagebox  # <-- V2.3 新增 messagebox
from PIL import Image, ImageTk

from definitions import GridType, Rarity, ItemClass, Element, ItemType, EFFECT_TYPES, CONDITION_TYPES

# --- 常量 (保持不变) ---
GRID_COLS, GRID_ROWS = 9, 7
GRID_CELL_SIZE = 35
EDITOR_ASSETS_FOLDER = "editor_assets"
WIKI_IMAGES_FOLDER = "wiki_images"

# --- V2.2 中文 <-> 英文 映射 (保持不变) ---
RARITY_EN_TO_ZH = {
    "COMMON": "普通", "RARE": "罕见", "EPIC": "史诗", "LEGENDARY": "传说",
    "GODLY": "神级", "UNIQUE": "特别"
}
CLASS_EN_TO_ZH = {
    "NEUTRAL": "通用", "RANGER": "游侠", "REAPER": "收割者",
    "PYROMANCER": "火焰魔导士", "BERSERKER": "狂战士", "MAGE": "魔法师",
    "ADVENTURER": "冒险家"
}
ELEMENT_EN_TO_ZH = {
    "MELEE": "近战", "RANGED": "远程", "EFFECT": "效果", "NATURE": "自然",
    "MAGIC": "魔法", "HOLY": "神圣", "DARK": "黑暗", "VAMPIRIC": "吸血",
    "FIRE": "火", "ICE": "冰", "TREASURE": "宝藏", "MUSICAL": "乐器"
}
TYPE_EN_TO_ZH = {
    "WEAPON": "武器", "SHIELD": "盾牌", "ACCESSORY": "配饰", "POTION": "魔药",
    "SPELL": "魔法卷轴", "FOOD": "食物", "BOOK": "魔法书", "PET": "宠物",
    "HELMET": "头盔", "ARMOR": "护甲", "GEMSTONE": "宝石", "SKILL": "技能",
    "GLOVE": "手套", "BACKPACK": "背包", "CARD": "卡牌", "SHOES": "鞋子",
    "CHESSPIECE": "棋子"
}
RARITY_ZH_TO_EN = {v: k for k, v in RARITY_EN_TO_ZH.items()}
CLASS_ZH_TO_EN = {v: k for k, v in CLASS_EN_TO_ZH.items()}
ELEMENT_ZH_TO_EN = {v: k for k, v in ELEMENT_EN_TO_ZH.items()}
TYPE_ZH_TO_EN = {v: k for k, v in TYPE_EN_TO_ZH.items()}
# ------------------------------------------

GRID_COLORS = {
    -1: "#2B2B2B", 0: "#343638", 1: "#A9A9A9",
    2: os.path.join(EDITOR_ASSETS_FOLDER, "star_a.png"),
    3: os.path.join(EDITOR_ASSETS_FOLDER, "star_b.png"),
    4: os.path.join(EDITOR_ASSETS_FOLDER, "star_c.png"),
}
BRUSH_NAMES = {-1: "背景", 0: "空格", 1: "实体", 2: "A星", 3: "B星", 4: "C星"}
STAR_EFFECT_KEYS = ["STAR_A_1", "STAR_A_2", "STAR_B_1", "STAR_B_2", "STAR_C_1", "STAR_C_2"]
LOGIC_OPTIONS = ["同时满足 (AND)", "满足任意 (OR)"]
STAR_TYPES_FOR_DROPDOWN = ["STAR_A", "STAR_B", "STAR_C"]
BOOL_CONDITIONS = ["requires_cooldown", "requires_start_of_battle", "requires_empty", "must_be_different"]


class ItemEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("背包乱斗 - 高级物品编辑器 (V2.3 合并导入版)")  # <-- 更新标题
        self.geometry("1400x900")
        ctk.set_appearance_mode("dark")

        self.items_data = self.load_json()  # 加载现有的 items.json
        self.current_item_key = None
        self.shape_matrix_data = [[-1 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.active_brush = -1
        self.effect_widgets = {}

        self.grid_icons = {}
        self.palette_icons = {}
        self.loaded_item_image = None
        self._load_editor_assets()

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.input_frame = ctk.CTkFrame(self, corner_radius=10)
        self.input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.item_list_frame = ctk.CTkFrame(self, corner_radius=10)
        self.item_list_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        self.create_input_widgets()
        self.create_item_list_widgets()  # 会调用 populate_item_list 显示 items.json 内容

    # (_load_editor_assets, _create_color_image 基本不变)
    def _load_editor_assets(self):
        print("正在加载编辑器资源...")
        for value, path_or_color in GRID_COLORS.items():
            try:
                if str(path_or_color).endswith(".png"):
                    if not os.path.exists(path_or_color):
                        print(f"警告: 找不到图标 {path_or_color}!")
                        continue

                    img_grid = Image.open(path_or_color).convert("RGBA")  # 确保 alpha 通道
                    img_grid = img_grid.resize((GRID_CELL_SIZE, GRID_CELL_SIZE), Image.Resampling.LANCZOS)
                    self.grid_icons[value] = ctk.CTkImage(light_image=img_grid, dark_image=img_grid,
                                                          size=(GRID_CELL_SIZE, GRID_CELL_SIZE))

                    img_palette = Image.open(path_or_color).convert("RGBA")
                    img_palette = img_palette.resize((50, 35), Image.Resampling.LANCZOS)
                    self.palette_icons[value] = ctk.CTkImage(light_image=img_palette, dark_image=img_palette,
                                                             size=(50, 35))
                else:
                    pass
            except Exception as e:
                print(f"加载图标 {path_or_color} 失败: {e}")

        self.grid_icons[-1] = self._create_color_image(GRID_COLORS[-1], (GRID_CELL_SIZE, GRID_CELL_SIZE))
        self.grid_icons[0] = self._create_color_image(GRID_COLORS[0], (GRID_CELL_SIZE, GRID_CELL_SIZE))
        self.grid_icons[1] = self._create_color_image(GRID_COLORS[1], (GRID_CELL_SIZE, GRID_CELL_SIZE))

        self.placeholder_image = self._create_color_image("#333", (100, 100), "无图片")

    def _create_color_image(self, color, size, text=None):
        img = Image.new('RGBA', size, color)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)

    def load_json(self):
        try:
            # 尝试加载 items.json
            if os.path.exists('items.json'):
                with open('items.json', 'r', encoding='utf-8') as f:
                    print("加载现有的 items.json ...")
                    return json.load(f)
            else:
                print("未找到 'items.json', 将创建一个空数据库。")
                return {}  # 如果 items.json 不存在，返回空字典
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载 'items.json' 失败: {e}。将创建一个空数据库。")
            return {}

    # (create_input_widgets 基本不变, 确保所有中文标签正确)
    def create_input_widgets(self):
        form_frame = ctk.CTkScrollableFrame(self.input_frame)
        form_frame.pack(expand=True, fill="both", padx=15, pady=15)

        self.item_image_label = ctk.CTkLabel(form_frame, text="", image=self.placeholder_image, width=100, height=100)
        self.item_image_label.grid(row=0, column=0, padx=5, pady=5, sticky="n")

        ctk.CTkLabel(form_frame, text="物品名称:").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.name_entry = ctk.CTkEntry(form_frame, width=250)
        self.name_entry.grid(row=0, column=2, padx=5, pady=5, columnspan=2)

        ctk.CTkLabel(form_frame, text="基础分数:").grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.score_entry = ctk.CTkEntry(form_frame, width=100)
        self.score_entry.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        self.cooldown_var = ctk.StringVar(value="off")
        self.cooldown_checkbox = ctk.CTkCheckBox(form_frame, text="有冷却", variable=self.cooldown_var, onvalue="on",
                                                 offvalue="off")
        self.cooldown_checkbox.grid(row=1, column=3, padx=10, pady=5, sticky="w")

        self.start_of_battle_var = ctk.StringVar(value="off")
        self.start_of_battle_checkbox = ctk.CTkCheckBox(form_frame, text="开局触发", variable=self.start_of_battle_var,
                                                        onvalue="on", offvalue="off")
        self.start_of_battle_checkbox.grid(row=1, column=4, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(form_frame, text="稀有度:").grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.rarity_var = ctk.StringVar(value=RARITY_EN_TO_ZH.get("COMMON", "普通"))
        rarity_options = list(RARITY_EN_TO_ZH.values())
        self.rarity_menu = ctk.CTkOptionMenu(form_frame, values=rarity_options, variable=self.rarity_var)
        self.rarity_menu.grid(row=2, column=2, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(form_frame, text="职业:").grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.class_var = ctk.StringVar(value=CLASS_EN_TO_ZH.get("NEUTRAL", "通用"))
        class_options = list(CLASS_EN_TO_ZH.values())
        self.class_menu = ctk.CTkOptionMenu(form_frame, values=class_options, variable=self.class_var)
        self.class_menu.grid(row=3, column=2, padx=5, pady=5, sticky="w")

        self.element_vars = {}
        ctk.CTkLabel(form_frame, text="元素:").grid(row=4, column=1, padx=5, pady=10, sticky="w")
        element_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        element_frame.grid(row=4, column=2, columnspan=3, padx=5, pady=10, sticky="w")
        for i, (en_name, zh_name) in enumerate(ELEMENT_EN_TO_ZH.items()):
            var = ctk.StringVar(value="off")
            cb = ctk.CTkCheckBox(element_frame, text=zh_name, variable=var, onvalue="on", offvalue="off")
            cb.grid(row=i // 4, column=i % 4, padx=5, pady=2, sticky="w")
            self.element_vars[en_name] = var

        self.type_vars = {}
        ctk.CTkLabel(form_frame, text="类型:").grid(row=5, column=1, padx=5, pady=10, sticky="w")
        type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        type_frame.grid(row=5, column=2, columnspan=3, padx=5, pady=10, sticky="w")
        for i, (en_name, zh_name) in enumerate(TYPE_EN_TO_ZH.items()):
            var = ctk.StringVar(value="off")
            cb = ctk.CTkCheckBox(type_frame, text=zh_name, variable=var, onvalue="on", offvalue="off")
            cb.grid(row=i // 4, column=i % 4, padx=5, pady=2, sticky="w")
            self.type_vars[en_name] = var

        ctk.CTkLabel(form_frame, text="形状矩阵:").grid(row=6, column=0, padx=5, pady=10, sticky="nw")
        shape_container = ctk.CTkFrame(form_frame, fg_color="transparent");
        shape_container.grid(row=6, column=1, columnspan=4, padx=5, pady=10, sticky="w")
        self.grid_frame = ctk.CTkFrame(shape_container);
        self.grid_frame.pack(side="left");
        self.grid_buttons = []
        for r in range(GRID_ROWS):
            row_btns = []
            for c in range(GRID_COLS):
                btn = ctk.CTkButton(self.grid_frame, text="", image=self.grid_icons[-1],
                                    width=GRID_CELL_SIZE, height=GRID_CELL_SIZE,
                                    corner_radius=0, fg_color=GRID_COLORS[-1],
                                    command=lambda r=r, c=c: self.paint_grid_cell(r, c))
                btn.grid(row=r, column=c, padx=1, pady=1);
                row_btns.append(btn)
            self.grid_buttons.append(row_btns)

        palette_frame = ctk.CTkFrame(shape_container, fg_color="transparent");
        palette_frame.pack(side="left", padx=20);
        self.palette_buttons = {}
        for val, name in BRUSH_NAMES.items():
            icon_to_use = self.palette_icons.get(val)
            color_to_use = GRID_COLORS[val] if not str(GRID_COLORS[val]).endswith(".png") else "#555"

            btn = ctk.CTkButton(palette_frame, text=name,
                                image=icon_to_use, fg_color=color_to_use,
                                compound="top",
                                command=lambda v=val: self.select_brush(v))
            btn.pack(pady=3, fill="x");
            self.palette_buttons[val] = btn

        ctk.CTkLabel(form_frame, text="效果定义:").grid(row=7, column=0, padx=5, pady=10, sticky="nw")
        self.effect_tab_view = ctk.CTkTabview(form_frame, width=700);
        self.effect_tab_view.grid(row=7, column=1, columnspan=4, padx=5, pady=10, sticky="w")
        self.effect_tab_view.add("星号效果");
        self.effect_tab_view.add("被动效果")

        self.star_effect_tab_view = ctk.CTkTabview(self.effect_tab_view.tab("星号效果"));
        self.star_effect_tab_view.pack(expand=True, fill="both")
        for star_key in STAR_EFFECT_KEYS: self.star_effect_tab_view.add(star_key)

        for star_key in STAR_EFFECT_KEYS: self._create_effect_ui(self.star_effect_tab_view.tab(star_key), star_key)
        self._create_effect_ui(self.effect_tab_view.tab("被动效果"), "passive_effects")

        self.select_brush(-1)
        self.clear_fields()

    # (_create_effect_ui, _add_effect_frame, _remove_effect_frame, _move_effect,
    #  _update_condition_value_widget, _add_condition_row 保持不变)
    def _create_effect_ui(self, parent, key):
        self.effect_widgets[key] = {'scroll_frame': None, 'effects': []}
        scroll_frame = ctk.CTkScrollableFrame(parent, label_text=f"{key} 的效果列表")
        scroll_frame.pack(expand=True, fill="both", padx=5, pady=5)
        self.effect_widgets[key]['scroll_frame'] = scroll_frame
        ctk.CTkButton(parent, text="+ 添加效果",
                      command=lambda p=scroll_frame, k=key: self._add_effect_frame(p, k)).pack(pady=5, padx=5,
                                                                                               side="bottom")

    def _add_effect_frame(self, parent, key, effect_data=None):
        effect_frame = ctk.CTkFrame(parent, border_width=1)
        effect_frame.pack(pady=5, padx=5, fill="x", expand=True)
        effect_frame.grid_columnconfigure(1, weight=1)

        control_frame = ctk.CTkFrame(effect_frame, fg_color="transparent")
        control_frame.grid(row=0, column=2, padx=5, pady=5, sticky="ne")
        ctk.CTkButton(control_frame, text="↑", width=25,
                      command=lambda f=effect_frame, p=parent: self._move_effect(p, f, "up")).pack(side="left")
        ctk.CTkButton(control_frame, text="↓", width=25,
                      command=lambda f=effect_frame, p=parent: self._move_effect(p, f, "down")).pack(side="left",
                                                                                                     padx=2)
        ctk.CTkButton(control_frame, text="X", width=25,
                      command=lambda f=effect_frame: self._remove_effect_frame(f, key)).pack(side="left")

        ctk.CTkLabel(effect_frame, text="效果类型:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        effect_type_var = ctk.StringVar(
            value=effect_data.get('effect', EFFECT_TYPES[0]) if effect_data else EFFECT_TYPES[0])
        ctk.CTkOptionMenu(effect_frame, variable=effect_type_var, values=EFFECT_TYPES).grid(row=0, column=1, padx=5,
                                                                                            pady=2, sticky="w")

        simple_value_entry = ctk.CTkEntry(effect_frame)
        dynamic_value_frame = ctk.CTkFrame(effect_frame, fg_color="transparent")

        def toggle_value_type():
            if dynamic_var.get() == "on":
                simple_value_entry.grid_remove()
                dynamic_value_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5)
            else:
                dynamic_value_frame.grid_remove()
                simple_value_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        dynamic_var = ctk.StringVar(value="off")
        dynamic_checkbox = ctk.CTkCheckBox(effect_frame, text="动态数值", variable=dynamic_var, onvalue="on",
                                           offvalue="off", command=toggle_value_type)
        dynamic_checkbox.grid(row=1, column=0, padx=5, pady=2, sticky="w")

        ctk.CTkLabel(dynamic_value_frame, text="基础值:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        base_value_entry = ctk.CTkEntry(dynamic_value_frame, width=100)
        base_value_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ctk.CTkLabel(dynamic_value_frame, text="加成来源星:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        per_star_var = ctk.StringVar(value=STAR_TYPES_FOR_DROPDOWN[0])
        per_star_menu = ctk.CTkOptionMenu(dynamic_value_frame, variable=per_star_var, values=STAR_TYPES_FOR_DROPDOWN)
        per_star_menu.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ctk.CTkLabel(dynamic_value_frame, text="每个加值:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        add_value_entry = ctk.CTkEntry(dynamic_value_frame, width=100)
        add_value_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")

        ctk.CTkLabel(effect_frame, text="条件逻辑:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        logic_var = ctk.StringVar(value=LOGIC_OPTIONS[0])
        ctk.CTkOptionMenu(effect_frame, variable=logic_var, values=LOGIC_OPTIONS).grid(row=3, column=1, padx=5, pady=2,
                                                                                       sticky="w")

        conditions_frame = ctk.CTkFrame(effect_frame, fg_color="transparent")
        conditions_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(conditions_frame, text="触发条件:").pack(anchor="w")
        ctk.CTkButton(conditions_frame, text="+ 添加条件", height=20,
                      command=lambda p=conditions_frame, k=key: self._add_condition_row(p, k)).pack(anchor="w",
                                                                                                    pady=2)  # V2.3 传递 key

        effect_frame.widgets = {
            'effect_type': effect_type_var, 'logic': logic_var, 'conditions': [],
            'dynamic_var': dynamic_var, 'simple_value': simple_value_entry,
            'base_value': base_value_entry, 'per_star': per_star_var, 'add_value': add_value_entry
        }

        if effect_data:
            value = effect_data.get('value')
            if isinstance(value, dict) and "base" in value:
                dynamic_var.set("on")
                base_value_entry.insert(0, str(value.get("base", "")))
                if "dynamic_bonus" in value:
                    per_star_var.set(value["dynamic_bonus"].get("per_activated_star", STAR_TYPES_FOR_DROPDOWN[0]))
                    add_value_entry.insert(0, str(value["dynamic_bonus"].get("add", "")))
            else:
                simple_value_entry.insert(0, str(value if value is not None else ""))

            if effect_data.get("condition_logic", "AND") == "OR": logic_var.set(LOGIC_OPTIONS[1])
            if "condition" in effect_data:
                for k_cond, v_cond in effect_data["condition"].items(): self._add_condition_row(conditions_frame, key,
                                                                                                {"type": k_cond,
                                                                                                 "value": v_cond})  # V2.3 传递 key

        toggle_value_type()
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
            # 更新内部列表顺序 (V2.3 修正)
            key = None
            for k, v in self.effect_widgets.items():
                if v['scroll_frame'] == parent:
                    key = k
                    break
            if key:
                # 查找 frame_to_move 在 effects 列表中的索引
                try:
                    current_effects_index = self.effect_widgets[key]['effects'].index(frame_to_move)
                    # 从列表中移除并插入到新位置
                    self.effect_widgets[key]['effects'].pop(current_effects_index)
                    self.effect_widgets[key]['effects'].insert(new_index, frame_to_move)
                except ValueError:
                    print("警告：移动效果时未在内部列表中找到该框架！")

            # 重新打包
            for child in parent.pack_slaves(): child.pack_forget()
            for child in children: child.pack(pady=5, padx=5, fill="x", expand=True)

    def _update_condition_value_widget(self, widgets):
        cond_type = widgets['type_var'].get()

        if widgets.get('value_widget'):
            widgets['value_widget'].destroy()
            widgets['value_widget'] = None  # 清理引用
            # 清理旧的变量引用
            if 'value_var' in widgets: del widgets['value_var']
            if 'value_entry' in widgets: del widgets['value_entry']

        if cond_type == 'requires_element':
            options = list(ELEMENT_EN_TO_ZH.values())
            var = ctk.StringVar(value=options[0])
            widget = ctk.CTkOptionMenu(widgets['value_frame'], variable=var, values=options)
            widgets['value_var'] = var
        elif cond_type == 'requires_type':
            options = list(TYPE_EN_TO_ZH.values())
            var = ctk.StringVar(value=options[0])
            widget = ctk.CTkOptionMenu(widgets['value_frame'], variable=var, values=options)
            widgets['value_var'] = var
        elif cond_type in BOOL_CONDITIONS:
            options = ["True", "False"]
            var = ctk.StringVar(value=options[0])
            widget = ctk.CTkOptionMenu(widgets['value_frame'], variable=var, values=options)
            widgets['value_var'] = var
        else:  # requires_name 等
            widget = ctk.CTkEntry(widgets['value_frame'])
            widgets['value_entry'] = widget

        widget.pack(expand=True, fill="x")
        widgets['value_widget'] = widget

    # V2.3 更新：添加 key 参数
    def _add_condition_row(self, parent, key, condition_data=None):
        condition_row = ctk.CTkFrame(parent)
        condition_row.pack(fill="x", pady=2)

        type_var = ctk.StringVar(value=CONDITION_TYPES[0])
        # V2.3 修正：传递 widgets 字典给回调
        type_menu = ctk.CTkOptionMenu(condition_row, variable=type_var, values=CONDITION_TYPES,
                                      command=lambda choice, w=widgets: self._update_condition_value_widget(
                                          w))  # 使用 command 触发更新
        type_menu.pack(side="left", padx=5)

        value_frame = ctk.CTkFrame(condition_row, fg_color="transparent")
        value_frame.pack(side="left", padx=5, expand=True, fill="x")

        # V2.3 修正：销毁时同时从父控件的 widgets['conditions'] 列表中移除
        def remove_condition():
            parent_effect_frame = condition_row.master.master  # Frame -> Frame -> EffectFrame
            if hasattr(parent_effect_frame, 'widgets') and 'conditions' in parent_effect_frame.widgets:
                if widgets in parent_effect_frame.widgets['conditions']:
                    parent_effect_frame.widgets['conditions'].remove(widgets)
                    print(f"Removed condition widget from list for effect {key}")
                else:
                    print(f"Warning: Could not find condition widget in list for effect {key} during removal.")
            else:
                print(f"Warning: Could not access parent conditions list for effect {key} during removal.")
            condition_row.destroy()

        ctk.CTkButton(condition_row, text="x", width=25, command=remove_condition).pack(side="right",
                                                                                        padx=5)  # V2.3 使用新函数

        widgets = {'frame': condition_row, 'type_var': type_var, 'value_frame': value_frame}
        # type_var.trace_add("write", lambda *args, w=widgets: self._update_condition_value_widget(w)) # trace_add 有时不稳定，改用 command

        if condition_data:
            type_var.set(condition_data.get("type", CONDITION_TYPES[0]))

        self._update_condition_value_widget(widgets)  # 初始化控件

        if condition_data:
            value = condition_data.get("value")
            value_str = str(value)

            cond_type = widgets['type_var'].get()
            if cond_type == 'requires_element' and value in ELEMENT_EN_TO_ZH:
                value_str = ELEMENT_EN_TO_ZH[value]
            elif cond_type == 'requires_type' and value in TYPE_EN_TO_ZH:
                value_str = TYPE_EN_TO_ZH[value]
            elif isinstance(value, list):  # 处理 requires_name 列表
                value_str = ", ".join(value)

            if 'value_var' in widgets:
                # 确保值在选项中
                if value_str in widgets['value_widget'].cget("values"):
                    widgets['value_var'].set(value_str)
                else:
                    print(f"警告：值 '{value_str}' 不在条件 '{cond_type}' 的选项中。")
                    # 可以设置一个默认值或保持为空
            elif 'value_entry' in widgets:
                widgets['value_entry'].insert(0, value_str)

        # V2.3 修正：查找正确的父效果控件
        parent_effect_frame = condition_row.master.master  # Frame -> Frame -> EffectFrame
        if hasattr(parent_effect_frame, 'widgets') and 'conditions' in parent_effect_frame.widgets:
            parent_effect_frame.widgets['conditions'].append(widgets)
        else:
            print(f"警告：无法将条件控件添加到效果框架 '{key}'！")

    def create_item_list_widgets(self):
        ctk.CTkLabel(self.item_list_frame, text="物品列表", font=("", 18, "bold")).pack(pady=(10, 5))

        self.search_entry = ctk.CTkEntry(self.item_list_frame, placeholder_text="搜索物品...")
        self.search_entry.pack(pady=5, padx=10, fill="x")
        self.search_entry.bind("<KeyRelease>", self.populate_item_list)

        self.list_scroll_frame = ctk.CTkScrollableFrame(self.item_list_frame)
        self.list_scroll_frame.pack(expand=True, fill="both", padx=10, pady=5)

        action_frame = ctk.CTkFrame(self.item_list_frame, fg_color="transparent")
        action_frame.pack(pady=10)
        ctk.CTkButton(action_frame, text="保存/更新物品", command=self.save_item).pack(pady=5, fill="x")
        ctk.CTkButton(action_frame, text="删除当前物品", fg_color="#D2691E", hover_color="#B85C1A",
                      command=self.delete_item).pack(pady=5, fill="x")

        io_frame = ctk.CTkFrame(action_frame)
        io_frame.pack(pady=(15, 5), fill="x")
        io_frame.grid_columnconfigure((0, 1), weight=1)  # 让两个按钮平分空间

        # V2.3 更新：修改导入按钮布局
        ctk.CTkButton(io_frame, text="导入(覆盖)...", command=self.import_json).grid(row=0, column=0, padx=(0, 5),
                                                                                     pady=(0, 5),
                                                                                     sticky="ew")  # <-- 改为 grid
        ctk.CTkButton(io_frame, text="导入(合并)...", command=self.merge_import_json).grid(row=0, column=1, padx=(5, 0),
                                                                                           pady=(0, 5),
                                                                                           sticky="ew")  # <-- V2.3 新增按钮
        ctk.CTkButton(io_frame, text="导出到 JSON...", command=self.export_json).grid(row=1, column=0, columnspan=2,
                                                                                      pady=0,
                                                                                      sticky="ew")  # <-- 改为 grid

        ctk.CTkButton(action_frame, text="清空表单", fg_color="gray50", hover_color="gray30",
                      command=self.clear_fields).pack(pady=5, fill="x")
        self.populate_item_list()  # 初始加载

    def import_json(self):
        """ V2.3 更新：此函数现在执行“覆盖”导入 """
        filepath = filedialog.askopenfilename(title="导入物品 JSON (覆盖)",
                                              filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")))
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.items_data = json.load(f)  # 直接覆盖
            print(f"成功从 {filepath} 覆盖导入物品")
            self.populate_item_list()
            self.clear_fields()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"导入文件出错: {e}")

    # --- V2.3 新增：合并导入函数 ---
    def merge_import_json(self):
        """ 加载一个 JSON 文件并将其内容合并到当前的 items_data 中 """
        filepath = filedialog.askopenfilename(title="导入物品 JSON (合并)",
                                              filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")))
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                new_data = json.load(f)

            merged_count = 0
            skipped_count = 0
            # 遍历新数据中的每个物品
            for item_key, item_value in new_data.items():
                if item_key not in self.items_data:
                    # 如果当前数据中不存在这个 key，直接添加
                    self.items_data[item_key] = item_value
                    merged_count += 1
                else:
                    # 如果已存在，跳过（可以选择覆盖，但跳过更安全）
                    skipped_count += 1

            print(f"成功从 {filepath} 合并导入物品:")
            print(f"  - 新增: {merged_count} 个")
            print(f"  - 跳过 (已存在): {skipped_count} 个")

            self.populate_item_list()  # 更新列表显示
            self.clear_fields()  # 清空表单

            # 可选：提示用户合并完成
            messagebox.showinfo("合并完成", f"合并导入完成。\n新增: {merged_count}\n跳过: {skipped_count}")

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"合并导入文件出错: {e}")
            messagebox.showerror("导入错误", f"合并导入文件时出错:\n{e}")

    # --- V2.3 新增结束 ---

    # (export_json, populate_item_list, select_brush, paint_grid_cell 基本不变)
    def export_json(self):
        # 确定默认文件名 (例如 items_backup_时间戳.json)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_filename = f"items_export_{timestamp}.json"

        filepath = filedialog.asksaveasfilename(
            title="导出物品到 JSON",
            initialfile=default_filename,  # V2.3 新增默认文件名
            defaultextension=".json",
            filetypes=(("JSON 文件", "*.json"), ("所有文件", "*.*")))
        if not filepath: return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.items_data, f, indent=2, ensure_ascii=False)
            print(f"成功导出当前 {len(self.items_data)} 个物品到 {filepath}")
        except Exception as e:
            print(f"导出文件出错: {e}")

    def populate_item_list(self, event=None):
        for widget in self.list_scroll_frame.winfo_children(): widget.destroy()
        search_term = self.search_entry.get().lower()
        # V2.3 优化: 直接对 items_data 操作
        filtered_items = {
            k: v for k, v in self.items_data.items()
            if search_term in v.get('name', k).lower() or search_term in str(k).lower()
        }
        # 按名字排序
        sorted_keys = sorted(filtered_items.keys(), key=lambda x: filtered_items[x].get('name', x))

        for item_key in sorted_keys:
            item_name = filtered_items[item_key].get('name', item_key)
            btn = ctk.CTkButton(self.list_scroll_frame, text=item_name,
                                command=lambda k=item_key: self.load_item_data(k),
                                fg_color="gray25")
            btn.pack(pady=2, fill="x")

    def select_brush(self, brush_value):
        self.active_brush = brush_value
        for val, btn in self.palette_buttons.items():
            btn.configure(border_width=3 if val == brush_value else 1)

    def paint_grid_cell(self, r, c):
        self.shape_matrix_data[r][c] = self.active_brush
        icon_to_use = self.grid_icons.get(self.active_brush, self.grid_icons[-1])
        color_to_use = "#333" if icon_to_use else (
            GRID_COLORS[self.active_brush] if not str(GRID_COLORS[self.active_brush]).endswith(".png") else "#555")

        self.grid_buttons[r][c].configure(image=icon_to_use, fg_color=color_to_use, text="")

    # (load_item_data 基本不变, 确保中文加载正确)
    def load_item_data(self, item_key):
        self.clear_fields()
        self.current_item_key = item_key
        data = self.items_data.get(item_key)
        if not data:
            print(f"错误：找不到物品 '{item_key}'")
            return

        item_image_filename = data.get("image_file")
        if item_image_filename:
            image_path = os.path.join(WIKI_IMAGES_FOLDER, item_image_filename)
            if os.path.exists(image_path):
                try:
                    img = Image.open(image_path).convert("RGBA")
                    img = img.resize((100, 100), Image.Resampling.LANCZOS)
                    self.loaded_item_image = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                    self.item_image_label.configure(image=self.loaded_item_image)
                except Exception as e:
                    print(f"加载物品图片 {image_path} 出错: {e}")
                    self.item_image_label.configure(image=self.placeholder_image)
            else:
                print(f"警告：找不到物品图片 {image_path}")
                self.item_image_label.configure(image=self.placeholder_image)
        else:
            self.item_image_label.configure(image=self.placeholder_image)

        self.name_entry.insert(0, data.get("name", item_key));
        self.score_entry.insert(0, str(data.get("base_score", 0)))

        rarity_en = data.get("rarity", "COMMON")
        self.rarity_var.set(RARITY_EN_TO_ZH.get(rarity_en, RARITY_EN_TO_ZH["COMMON"]))

        class_en = data.get("item_class", "NEUTRAL")
        self.class_var.set(CLASS_EN_TO_ZH.get(class_en, CLASS_EN_TO_ZH["NEUTRAL"]))

        if data.get("has_cooldown", False): self.cooldown_var.set("on")
        if data.get("is_start_of_battle", False): self.start_of_battle_var.set("on")

        # 先取消所有勾选
        for var in self.element_vars.values(): var.set("off")
        for var in self.type_vars.values(): var.set("off")

        for en_name in data.get("elements", []):
            if en_name in self.element_vars:
                self.element_vars[en_name].set("on")
            else:
                print(f"警告：物品 '{item_key}' 的元素 '{en_name}' 在 definitions.py 中不存在！")
        for en_name in data.get("types", []):
            if en_name in self.type_vars:
                self.type_vars[en_name].set("on")
            else:
                print(f"警告：物品 '{item_key}' 的类型 '{en_name}' 在 definitions.py 中不存在！")

        for key in self.effect_widgets:
            scroll_frame = self.effect_widgets[key]['scroll_frame']
            if scroll_frame:
                for widget in scroll_frame.winfo_children():
                    try:
                        widget.destroy()
                    except Exception:
                        pass
            self.effect_widgets[key]['effects'] = []

        for effect in data.get("passive_effects", []): self._add_effect_frame(
            self.effect_widgets["passive_effects"]['scroll_frame'], "passive_effects", effect)

        for star_key, effects in data.get("star_effects", {}).items():
            if star_key in self.effect_widgets:
                if isinstance(effects, dict): effects = [effects]
                for effect in effects:
                    self._add_effect_frame(self.effect_widgets[star_key]['scroll_frame'], star_key, effect)

        matrix = data.get("shape_matrix", []);
        h = len(matrix);
        w = len(matrix[0]) if h > 0 else 0
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                val = matrix[r][c] if r < h and c < w else -1
                self.shape_matrix_data[r][c] = val
                icon_to_use = self.grid_icons.get(val, self.grid_icons[-1])
                color_to_use = "#333" if icon_to_use else (
                    GRID_COLORS[val] if not str(GRID_COLORS[val]).endswith(".png") else "#555")
                self.grid_buttons[r][c].configure(image=icon_to_use, fg_color=color_to_use, text="")

    # (save_item, delete_item, clear_fields 基本不变, 确保中文转换正确)
    def save_item(self):
        item_name = self.name_entry.get()
        if not item_name:
            messagebox.showerror("错误", "物品名称不能为空！")  # V2.3 弹窗提示
            return

        item_key = self.current_item_key if self.current_item_key else item_name

        if self.current_item_key and self.current_item_key != item_name:
            # V2.3 弹窗确认
            if messagebox.askyesno("名称已更改",
                                   f"物品 '{self.current_item_key}' 的名称已更改为 '{item_name}'。\n是否使用新名称作为 Key 保存？\n(注意：这会删除旧 Key 的条目，如果它存在的话)"):
                print(f"物品 '{self.current_item_key}' 名称已更改为 '{item_name}'。将使用新名称作为 Key 保存。")
                if self.current_item_key in self.items_data:
                    del self.items_data[self.current_item_key]
                item_key = item_name
                self.current_item_key = item_name
            else:
                # 用户取消，恢复旧名称
                self.name_entry.delete(0, 'end')
                self.name_entry.insert(0, self.current_item_key)
                item_key = self.current_item_key
                item_name = self.current_item_key  # 确保下面使用的是旧名字
                print("名称更改已取消。")

        min_r, max_r, min_c, max_c = GRID_ROWS, -1, GRID_COLS, -1;
        has_content = False
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.shape_matrix_data[r][c] != -1: has_content = True; min_r = min(min_r, r); max_r = max(max_r,
                                                                                                              r); min_c = min(
                    min_c, c); max_c = max(max_c, c)
        trimmed_matrix = [
            [self.shape_matrix_data[r][c] if self.shape_matrix_data[r][c] != -1 else 0 for c in range(min_c, max_c + 1)]
            for r in range(min_r, max_r + 1)] if has_content else []

        existing_data = self.items_data.get(item_key, {})

        rarity_zh = self.rarity_var.get()
        rarity_en = RARITY_ZH_TO_EN.get(rarity_zh, "COMMON")

        class_zh = self.class_var.get()
        class_en = CLASS_ZH_TO_EN.get(class_zh, "NEUTRAL")

        elements_en = sorted([en_name for en_name, var in self.element_vars.items() if var.get() == "on"])
        types_en = sorted([en_name for en_name, var in self.type_vars.items() if var.get() == "on"])

        new_data = {
            "name": item_name,
            "image_file": existing_data.get("image_file"),
            "rarity": rarity_en,
            "item_class": class_en,
            "elements": elements_en,
            "types": types_en,
            "base_score": int(self.score_entry.get() or 0),
            "has_cooldown": self.cooldown_var.get() == "on",
            "is_start_of_battle": self.start_of_battle_var.get() == "on",
            "shape_matrix": trimmed_matrix,
            "passive_effects": [],
            "star_effects": {}
        }

        all_effect_keys = STAR_EFFECT_KEYS + ["passive_effects"]
        for key in all_effect_keys:
            effect_list = []
            if key not in self.effect_widgets or not self.effect_widgets[key]['scroll_frame']:
                print(f"警告：效果控件 '{key}' 未初始化！")
                continue

            scroll_frame = self.effect_widgets[key]['scroll_frame']

            # 检查内部列表是否一致
            if len(self.effect_widgets[key]['effects']) != len(scroll_frame.pack_slaves()):
                print(f"警告：效果控件内部列表与界面不一致 ({key})！")
                # 可以尝试重新同步或只处理内部列表

            for w in self.effect_widgets[key]['effects']:
                if isinstance(w, ctk.CTkFrame) and hasattr(w, 'widgets') and w.winfo_exists():
                    widgets = w.widgets
                    value = None
                    if widgets['dynamic_var'].get() == 'on':
                        try:
                            base = float(widgets['base_value'].get() or 0)
                            add = float(widgets['add_value'].get() or 0)
                            per_star = widgets['per_star'].get()
                            value = {"base": base, "dynamic_bonus": {"add": add, "per_activated_star": per_star}}
                        except ValueError:
                            print(f"警告：物品 '{item_name}' 的动态数值无效，已设为 0。")
                            value = {"base": 0.0}
                    else:
                        value_str = widgets['simple_value'].get()
                        if value_str:
                            try:
                                value = eval(value_str)
                            except (NameError, SyntaxError, TypeError):
                                value = value_str
                        else:
                            value = None

                    logic_str = "AND" if widgets['logic'].get() == LOGIC_OPTIONS[0] else "OR"
                    effect_data = {"effect": widgets['effect_type'].get(), "value": value, "condition_logic": logic_str}

                    conditions_dict = {}
                    if 'conditions' not in widgets: widgets['conditions'] = []

                    for cond in widgets['conditions']:
                        if isinstance(cond, dict) and 'frame' in cond and cond['frame'].winfo_exists():
                            cond_type = cond['type_var'].get()
                            cond_val_str = ""
                            cond_val = None
                            if 'value_var' in cond:
                                cond_val_str = cond['value_var'].get()
                                if cond_type == 'requires_element':
                                    cond_val = ELEMENT_ZH_TO_EN.get(cond_val_str)
                                elif cond_type == 'requires_type':
                                    cond_val = TYPE_ZH_TO_EN.get(cond_val_str)

                            elif 'value_entry' in cond:
                                cond_val_str = cond['value_entry'].get()

                            if cond_val is None:
                                try:
                                    if cond_val_str.lower() == 'true':
                                        cond_val = True
                                    elif cond_val_str.lower() == 'false':
                                        cond_val = False
                                    elif cond_type == 'requires_name' and (
                                            cond_val_str.startswith('[') or ',' in cond_val_str):
                                        cond_val = [name.strip().strip("'\"") for name in
                                                    cond_val_str.strip('[]').split(',')]
                                    else:
                                        cond_val = eval(cond_val_str)
                                except (NameError, SyntaxError, TypeError):
                                    cond_val = cond_val_str

                            if cond_val is not None and cond_val != "":
                                conditions_dict[cond_type] = cond_val

                    if conditions_dict:
                        effect_data["condition"] = conditions_dict

                    effect_list.append(effect_data)

            if key == "passive_effects":
                if effect_list: new_data["passive_effects"] = effect_list
            else:
                # 确保 star_effects 字典存在
                if effect_list:
                    if "star_effects" not in new_data: new_data["star_effects"] = {}
                    new_data["star_effects"][key] = effect_list

        self.items_data[item_key] = new_data

        try:
            with open('items.json', 'w', encoding='utf-8') as f:
                json.dump(self.items_data, f, indent=2, ensure_ascii=False)
            print(f"成功保存 '{item_name}' 到 items.json!")
        except Exception as e:
            print(f"保存 items.json 出错: {e}")
            messagebox.showerror("保存失败", f"保存 items.json 时出错:\n{e}")  # V2.3 弹窗

        self.populate_item_list();
        self.clear_fields()

    def delete_item(self):
        if self.current_item_key and self.current_item_key in self.items_data:
            item_name_to_delete = self.items_data[self.current_item_key].get('name', self.current_item_key)
            # V2.3 弹窗确认
            if messagebox.askyesno("确认删除", f"确定要删除物品 '{item_name_to_delete}' 吗？\n此操作不可撤销。"):
                del self.items_data[self.current_item_key]

                try:
                    with open('items.json', 'w', encoding='utf-8') as f:
                        json.dump(self.items_data, f, indent=2, ensure_ascii=False)
                    print(f"成功从 items.json 删除 '{item_name_to_delete}'!")
                except Exception as e:
                    print(f"删除后保存 items.json 出错: {e}")
                    messagebox.showerror("保存失败", f"删除后保存 items.json 时出错:\n{e}")  # V2.3 弹窗

                self.populate_item_list();
                self.clear_fields()
            else:
                print("删除操作已取消。")

    def clear_fields(self):
        self.name_entry.delete(0, 'end');
        self.score_entry.delete(0, 'end')
        self.rarity_var.set(RARITY_EN_TO_ZH.get("COMMON", "普通"))
        self.class_var.set(CLASS_EN_TO_ZH.get("NEUTRAL", "通用"))
        for var in self.element_vars.values(): var.set("off")
        for var in self.type_vars.values(): var.set("off")
        self.cooldown_var.set("off")
        self.start_of_battle_var.set("off")

        self.item_image_label.configure(image=self.placeholder_image)
        self.loaded_item_image = None

        for key in self.effect_widgets:
            scroll_frame = self.effect_widgets[key]['scroll_frame']
            if scroll_frame:
                for widget in scroll_frame.winfo_children():
                    try:
                        widget.destroy()
                    except Exception:
                        pass
            self.effect_widgets[key]['effects'] = []

        self.shape_matrix_data = [[-1 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                self.grid_buttons[r][c].configure(image=self.grid_icons[-1], fg_color=GRID_COLORS[-1], text="")

        self.current_item_key = None;
        self.select_brush(-1)


if __name__ == "__main__":
    # V2.3 确保依赖已安装
    try:
        from PIL import Image, ImageTk
    except ImportError:
        print("错误：缺少 Pillow 库。请在终端运行 'pip install pillow'")
        exit()

    app = ItemEditorApp()
    app.mainloop()