# -*- coding: utf-8 -*-
import json
import os
import re

# --- 配置 ---
# 输入文件
JS_DATA_FILE = "FAILED_items.json"  # 你手动修复过的、上次失败的 JS 数据
WIKI_DATA_FILE = "NEW_items_ALL.json"  # 包含中文名和图片名的查找表
# 输出文件
OUTPUT_FILE = "FIXED_items.json"  # 本次修复后成功合并的物品
OUTPUT_FAILED_FILE = "RE-FAILED_items.json"  # 修复后仍然匹配失败的物品

# --- 映射规则 (与 V3.3 版保持一致) ---
RARITY_JS_TO_JSON = {
    "Common": "COMMON", "Uncommon": "RARE", "Rare": "EPIC",
    "Epic": "LEGENDARY", "Legendary": "GODLY", "Unique": "UNIQUE",
    "Godly": "GODLY",
}
CLASS_JS_TO_JSON = {
    "Neutral": "NEUTRAL", "Ranger": "RANGER", "Reaper": "REAPER",
    "Pyromancer": "PYROMANCER", "Berserker": "BERSERKER", "Mage": "MAGE",
    "Adventurer": "ADVENTURER",
}
ELEMENT_JS_TO_JSON = {
    "Melee": "MELEE", "Ranged": "RANGED", "Effect": "EFFECT", "Nature": "NATURE",
    "Magic": "MAGIC", "Holy": "HOLY", "Dark": "DARK", "Vampiric": "VAMPIRIC",
    "Fire": "FIRE", "Ice": "ICE", "Treasure": "TREASURE", "Musical": "MUSICAL",
}
TYPE_JS_TO_JSON = {
    "Weapon": "WEAPON", "Shield": "SHIELD", "Accessory": "ACCESSORY", "Potion": "POTION",
    "Spell": "SPELL", "Scroll": "SPELL",
    "Food": "FOOD", "Book": "BOOK", "Pet": "PET",
    "Helmet": "HELMET", "Armor": "ARMOR", "Gemstone": "GEMSTONE", "Skill": "SKILL",
    "Glove": "GLOVE", "Gloves": "GLOVE",
    "Backpack": "BACKPACK", "Bag": "BACKPACK",
    "Card": "CARD", "Shoes": "SHOES",
    "ChessPiece": "CHESSPIECE", "Chess Piece": "CHESSPIECE",
    "Ranged Weapon": "WEAPON", "Melee Weapon": "WEAPON",
}


# --- 辅助函数 (保持不变) ---
def normalize_key_for_matching(input_string):
    if not input_string or not isinstance(input_string, str):
        return None
    normalized = re.sub(r'[^a-z0-9]', '', input_string.lower())
    return normalized


def create_lookup_from_wiki_json(wiki_file):
    lookup = {}
    print(f"正在从 {wiki_file} 创建 清理后的图片基本名 -> (中文名, 原始图片名) 查找表...")
    try:
        with open(wiki_file, 'r', encoding='utf-8') as f:
            wiki_data = json.load(f)

        for item_key, item_data in wiki_data.items():
            img_file = item_data.get("image_file")
            zh_name = item_data.get("name")
            if img_file and zh_name:
                base_name, _ = os.path.splitext(img_file)
                normalized_key = normalize_key_for_matching(base_name)
                if normalized_key:
                    if normalized_key in lookup:
                        print(
                            f"警告：清理后的图片基本名 '{normalized_key}' (来自 {img_file}) 重复。旧中文名: '{lookup[normalized_key]['zh_name']}', 新中文名: '{zh_name}'。将使用后者。")
                    lookup[normalized_key] = {"zh_name": zh_name, "original_img_file": img_file}
                else:
                    print(f"警告：无法从图片名 '{img_file}' 生成有效的查找键。")
            else:
                pass
        print(f"查找表创建完成，包含 {len(lookup)} 个唯一图片基本名条目。")
        return lookup

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"错误：无法加载或解析 {wiki_file}: {e}")
        return None
    except Exception as e:
        print(f"创建查找表时发生意外错误: {e}")
        return None


# --- 主合并与转换逻辑 ---
if __name__ == "__main__":
    # 1. 创建查找字典
    wiki_lookup = create_lookup_from_wiki_json(WIKI_DATA_FILE)
    if wiki_lookup is None:
        exit()

    # 2. 加载你修复过的 FAILED_items.json
    print(f"正在加载你修复过的 JS 数据文件: {JS_DATA_FILE}")
    js_data_list = None
    try:
        with open(JS_DATA_FILE, 'r', encoding='utf-8') as f:
            js_data_list = json.load(f)
        if not isinstance(js_data_list, list):
            print(f"错误：'{JS_DATA_FILE}' 的内容不是一个 JSON 列表。")
            exit()
        print(f"成功加载 {len(js_data_list)} 个待修复的物品条目。")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"错误：无法加载或解析 {JS_DATA_FILE}: {e}")
        exit()

    # 3. 合并与转换
    final_items_db = {}  # 存放本次修复成功的
    failed_items_list = []  # 存放本次仍然失败的
    success_count = 0
    fail_count = 0
    failed_names_for_log = []

    print(f"\n开始基于你修复后的 'name' 字段进行匹配与转换...")
    for js_item in js_data_list:
        if not isinstance(js_item, dict):
            continue

        # --- 获取用于匹配的 Key (基于你手动修复的 'name' 字段) ---
        js_name_en = js_item.get("name")
        match_key = normalize_key_for_matching(js_name_en)
        # ---------------------------------------------------

        if not match_key:
            print(f"警告：跳过一个没有有效英文名 'name' 的 JS 条目: {js_item.get('gid', 'N/A')}")
            fail_count += 1
            failed_names_for_log.append(f"JS GID {js_item.get('gid', 'N/A')} (无有效英文名)")
            failed_items_list.append(js_item)
            continue

        wiki_match_data = wiki_lookup.get(match_key)

        if wiki_match_data:
            # --- 匹配成功 ---
            zh_name = wiki_match_data["zh_name"]
            original_img_file = wiki_match_data["original_img_file"]
            item_key = zh_name

            # --- 提取和映射属性 (逻辑同 V3.3) ---
            js_rarity = js_item.get("rarity")
            rarity = RARITY_JS_TO_JSON.get(js_rarity, "COMMON")

            js_class_list = js_item.get("class", [])
            item_class = "NEUTRAL"
            if js_class_list and isinstance(js_class_list, list):
                item_class = CLASS_JS_TO_JSON.get(js_class_list[0], "NEUTRAL") if js_class_list else "NEUTRAL"

            js_elements = js_item.get("extraTypes", [])
            elements = sorted([ELEMENT_JS_TO_JSON.get(e) for e in js_elements if ELEMENT_JS_TO_JSON.get(e)])

            js_type = js_item.get("type")
            types = []
            if js_type:
                mapped_type = TYPE_JS_TO_JSON.get(js_type)
                if mapped_type:
                    types.append(mapped_type)
                elif " " in js_type:
                    no_space_type = js_type.replace(" ", "")
                    mapped_no_space = TYPE_JS_TO_JSON.get(no_space_type)
                    if mapped_no_space:
                        types.append(mapped_no_space)
                    else:
                        base_type = js_type.split(" ")[-1]
                        mapped_base_type = TYPE_JS_TO_JSON.get(base_type)
                        if mapped_base_type:
                            types.append(mapped_base_type)
                        else:
                            print(f"警告：物品 '{zh_name}' (英文: {js_name_en}) 的类型 '{js_type}' 无法完全映射。")
                else:
                    print(f"警告：物品 '{zh_name}' (英文: {js_name_en}) 的类型 '{js_type}' 无法映射。")
            if not types and js_type:
                if TYPE_JS_TO_JSON.get(js_type):
                    types.append(TYPE_JS_TO_JSON.get(js_type))
                else:
                    print(
                        f"严重警告：物品 '{zh_name}' (英文: {js_name_en}) 的类型 '{js_type}' 仍然完全未能映射到已知类型！")

            shape_matrix = js_item.get("shape", [[1]])
            raw_effect_string = js_item.get("effect", "")
            has_cooldown = "cd" in js_item or "冷却" in raw_effect_string or "Every " in raw_effect_string
            is_start_of_battle = "战斗开始时" in raw_effect_string or "Start of battle:" in raw_effect_string

            base_score = 0
            passive_effects = []
            star_effects = {}

            # --- 构建最终条目 ---
            final_item = {
                "name": zh_name,
                "image_file": original_img_file,
                "rarity": rarity,
                "item_class": item_class,
                "elements": elements,
                "types": sorted(list(set(types))),
                "base_score": base_score,
                "has_cooldown": has_cooldown,
                "is_start_of_battle": is_start_of_battle,
                "shape_matrix": shape_matrix,
                "passive_effects": passive_effects,
                "star_effects": star_effects,
                "raw_effect_string": raw_effect_string
            }
            # --- 构建结束 ---

            if item_key in final_items_db:
                print(f"警告：物品 Key '{item_key}' 重复！将覆盖之前的条目。")
            final_items_db[item_key] = final_item
            success_count += 1
        else:
            # --- 匹配失败 ---
            fail_count += 1
            failed_names_for_log.append(f"'{js_name_en}' (Normalized Key: '{match_key}')")
            failed_items_list.append(js_item)

    print(f"\n--- 修复批次合并完成 ---")
    print(f"总共处理了 {len(js_data_list)} 个来自 '{JS_DATA_FILE}' 的物品。")
    print(f"成功匹配并写入: {success_count} 个")
    print(f"未能匹配 (已跳过): {fail_count} 个")
    if failed_names_for_log:
        print("\n以下 JS 物品【仍然】未能找到匹配的中文名/图片名:")
        for failed_name_info in failed_names_for_log:
            print(f"  - {failed_name_info}")

    # 4. 保存最终结果 (成功匹配的)
    print(f"\n正在将 {success_count} 个成功匹配的物品写入到: {OUTPUT_FILE}")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_items_db, f, indent=2, ensure_ascii=False)
        print(f"--- 成功! ---")
        print(f"修复后合并的物品数据已保存到 '{OUTPUT_FILE}'。")

    except IOError as e:
        print(f"保存文件 '{OUTPUT_FILE}' 失败: {e}")

    # 5. 保存仍然失败的结果
    if failed_items_list:
        print(f"\n正在将 {fail_count} 个【仍然】未能匹配的物品原始 JS 数据写入到: {OUTPUT_FAILED_FILE}")
        try:
            with open(OUTPUT_FAILED_FILE, 'w', encoding='utf-8') as f:
                json.dump(failed_items_list, f, indent=2, ensure_ascii=False)
            print(f"--- 成功! ---")
            print(f"仍然匹配失败的物品数据已保存到 '{OUTPUT_FAILED_FILE}' 供您再次检查。")
        except IOError as e:
            print(f"保存失败文件 '{OUTPUT_FAILED_FILE}' 失败: {e}")

    print("\n--- 下一步 ---")
    print(f"1. 检查 '{OUTPUT_FILE}' 文件是否包含了你修复的物品。")
    print(f"2. 运行 'editor.py' (V2.3 或更高版本)。")
    print(f"3. 使用 [从 JSON 导入...] 加载 'FINAL_items.json' (你上次成功的主文件)。")
    print(f"4. 使用 [导入(合并)...] 按钮加载 '{OUTPUT_FILE}' (你刚生成的修复文件)。")
    print(f"5. 你的编辑器中现在应该有了完整的 {392 + success_count} 个物品。")
    print(f"6. (如果 {fail_count} > 0) 检查 '{RE - FAILED_items.json}'，看是否需要再次修复。")