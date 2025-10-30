import requests
import json
import re
import os
import shutil
import time  # 导入 time 模块

# --- 映射字典 (保持不变) ---
RARITY_MAP = {
    "普通": "COMMON", "罕见": "RARE", "史诗": "EPIC", "传说": "LEGENDARY",
    "传奇": "LEGENDARY", "神级": "GODLY", "特别": "UNIQUE",
}
CLASS_MAP = {
    "通用": "NEUTRAL", "中立": "NEUTRAL", "游侠": "RANGER", "收割者": "REAPER",
    "火焰魔导士": "PYROMANCER", "狂战士": "BERSERKER", "魔法师": "MAGE", "冒险家": "ADVENTURER",
}
ELEMENT_MAP = {
    "近战": "MELEE", "远程": "RANGED", "效果": "EFFECT", "自然": "NATURE",
    "魔法属性": "MAGIC", "魔法": "MAGIC", "神圣": "HOLY", "黑暗": "DARK",
    "暗": "DARK", "吸血属性": "VAMPIRIC", "吸血": "VAMPIRIC", "火": "FIRE",
    "冰": "ICE", "乐器": "MUSICAL", "宝藏": "TREASURE"
}
TYPE_MAP = {
    "配饰": "ACCESSORY", "武器": "WEAPON", "护甲": "ARMOR", "食物": "FOOD",
    "宝石": "GEMSTONE", "手套": "GLOVE", "头盔": "HELMET", "宠物": "PET",
    "魔药": "POTION", "盾牌": "SHIELD", "技能": "SKILL", "魔法卷轴": "SPELL",
    "魔法书": "BOOK", "书": "BOOK", "背包": "BACKPACK", "卡牌": "CARD",
    "鞋子": "SHOES", "棋子": "CHESSPIECE",
}

# --- V4 版请求头 (保持不变) ---
WIKI_IMAGE_BASE_URL = "https://backpackbattles.wiki.gg/zh/wiki/Special:Filepath/"
IMAGE_DOWNLOAD_FOLDER = "wiki_images"
REQUEST_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/125.0.0.0 Safari/537.36'),
    'Referer': 'https://backpackbattles.wiki.gg/zh/wiki/Special:CargoTables/Items'
}


# -----------------------------

def parse_grid_simple(grid_str):
    if grid_str == "1":
        return [[1]]
    return [[1]]


def get_wiki_data():
    API_URL = "https://backpackbattles.wiki.gg/zh/api.php"

    fields = ("name, image, rarity, itemtype, icontype, class, cost, effect, grid, "
              "mindamage, maxdamage, cooldown, stamina, accuracy, sockets, addshop, tags")

    PARAMS = {
        "action": "cargoquery",
        "tables": "Items",
        "fields": fields,
        "format": "json",
        "limit": 500  # <-- V6: 确保这里是 500 (抓取全部)
    }

    try:
        print(f"正在抓取 {PARAMS['limit']} 条物品数据...")
        response = requests.get(API_URL, params=PARAMS, headers=REQUEST_HEADERS)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            print(f"API Error: {data['error']['info']}")
            return None
        return data["cargoquery"]

    except requests.exceptions.RequestException as e:
        print(f"Error fetching wiki data: {e}")
        return None


def convert_to_project_format(wiki_items):
    new_items_db = {}
    print(f"开始转换 {len(wiki_items)} 个物品...")

    for item_entry in wiki_items:
        data = item_entry["title"]
        name = data.get("name")
        if not name:
            print("Skipping item with no name.")
            continue

        item_key = re.sub(r'[^A-Za-z0-9]', '', name)
        if not item_key:
            item_key = name

        wiki_rarity = data.get("rarity", "普通")
        rarity = RARITY_MAP.get(wiki_rarity, "COMMON")

        wiki_class_list = data.get("class", "中立").split(',')
        item_class = "NEUTRAL"
        for wc in wiki_class_list:
            clean_wc = wc.strip()
            if clean_wc in CLASS_MAP:
                item_class = CLASS_MAP[clean_wc]
                break

        wiki_elements = data.get("icontype", "").split(',')
        elements = [ELEMENT_MAP[e.strip()] for e in wiki_elements if e.strip() in ELEMENT_MAP]

        wiki_types = data.get("itemtype", "").split(',')
        types = [TYPE_MAP[t.strip()] for t in wiki_types if t.strip() in TYPE_MAP]

        effect_text = data.get("effect", "")
        has_cooldown = data.get("cooldown") or "冷却" in effect_text
        is_start_of_battle = "战斗开始时" in effect_text

        shape_matrix = parse_grid_simple(data.get("grid", ""))

        passive_effects = []
        star_effects = {}
        base_score = 0

        image_filename = data.get("image")

        new_item = {
            "name": name,
            "image_file": image_filename,
            "rarity": rarity,
            "item_class": item_class,
            "elements": sorted(list(set(elements))),
            "types": sorted(list(set(types))),
            "base_score": base_score,
            "has_cooldown": bool(has_cooldown),
            "is_start_of_battle": is_start_of_battle,
            "shape_matrix": shape_matrix,
            "passive_effects": passive_effects,
            "star_effects": star_effects
        }

        new_items_db[item_key] = new_item

    print(f"成功转换 {len(new_items_db)} 个物品。")
    return new_items_db


def download_all_images(new_database, output_folder):
    print(f"\n开始下载图片到 '{output_folder}' 文件夹...")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"创建文件夹: {output_folder}")

    downloaded_count = 0
    failed_count = 0

    image_files_to_download = set()
    for item in new_database.values():
        if item.get("image_file"):
            image_files_to_download.add(item["image_file"])

    total_images = len(image_files_to_download)
    print(f"共找到 {total_images} 张不重复的图片需要下载。")

    for i, filename in enumerate(image_files_to_download):
        if not filename:
            continue

        image_url = WIKI_IMAGE_BASE_URL + filename
        save_path = os.path.join(output_folder, filename)

        if os.path.exists(save_path):
            print(f"({i + 1}/{total_images}) [跳过] {filename} 已存在。")
            downloaded_count += 1
            continue

        # --- V6: 自动重试逻辑 ---
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # --- V6 修改：增加基础等待时间 ---
                wait_time = 1.5  # 增加到 1.5 秒
                print(f"({i + 1}/{total_images}) 准备下载 {filename} (等待 {wait_time} 秒)...")
                time.sleep(wait_time)
                # ---------------------------------

                response = requests.get(image_url, headers=REQUEST_HEADERS, stream=True)
                response.raise_for_status()  # 这将捕获 4xx 和 5xx 错误

                with open(save_path, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)

                print(f"({i + 1}/{total_images}) [成功] {filename}")
                downloaded_count += 1
                break  # 成功，跳出重试循环

            except requests.exceptions.RequestException as e:
                # 检查是不是 429 错误
                if e.response is not None and e.response.status_code == 429:
                    wait_seconds = 30  # 429 错误，长时间等待
                    print(
                        f"({i + 1}/{total_images}) [警告] 遭遇 429 限速！正在等待 {wait_seconds} 秒后重试 (第 {attempt + 1}/{max_retries} 次)...")
                    time.sleep(wait_seconds)
                else:
                    # 其他错误 (如 404, 500), 直接失败
                    print(f"({i + 1}/{total_images}) [失败] {filename} (Error: {e})")
                    failed_count += 1
                    break  # 失败，跳出重试循环

            # 如果循环 3 次都失败了 (都是429)
            if attempt == max_retries - 1:
                print(f"({i + 1}/{total_images}) [失败] {filename} (重试 3 次后仍然 429 限速)")
                failed_count += 1
        # --- V6 重试逻辑结束 ---

    print(f"\n图片下载完成。 成功: {downloaded_count}, 失败: {failed_count}")


def main():
    print("正在从 backpackbattles.wiki.gg 获取物品数据...")
    wiki_data = get_wiki_data()

    if not wiki_data:
        print("无法获取 wiki 数据。请检查网络连接或 API 限制。")
        return

    new_database = convert_to_project_format(wiki_data)

    download_all_images(new_database, IMAGE_DOWNLOAD_FOLDER)

    # --- V6: 确保你使用的是完整版的文件名 ---
    output_filename = "NEW_items_ALL.json"

    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(new_database, f, indent=2, ensure_ascii=False)

        print(f"\n--- 成功! ---")
        print(f"所有物品数据已保存到 '{output_filename}'。")
        print(f"所有物品图片已保存到 '{IMAGE_DOWNLOAD_FOLDER}/' 文件夹。")

        print("\n--- 【【【 警告：关键步骤 】】】 ---")
        print("在运行 editor.py 或 main.py 之前，【必须】先更新 'definitions.py' 文件，")
        print("否则程序会因为找不到新类型（如 'BACKPACK'）而崩溃。")
        print("\n请打开 'definitions.py' 文件，找到 'class ItemType(Enum):' 部分，")
        print("并【添加】以下缺失的行：")
        print('    BACKPACK = "Backpack"')
        print('    CARD = "Card"')
        print('    SHOES = "Shoes"')
        print('    CHESSPIECE = "ChessPiece"')

        print("\n--- 【下一步操作】 ---")
        print(f"1. (必做) 手动更新 'definitions.py' 文件。")
        print(f"2. 运行 'editor.py' (python editor.py)")
        print(f"3. 在编辑器中，点击 [Import from JSON...] 按钮")
        print(f"4. 选择刚刚生成的 '{output_filename}' 文件")
        print(f"5. 手动修复每个物品的形状 (Shape Matrix) 和效果 (Effects)。")

    except IOError as e:
        print(f"保存文件失败: {e}")


if __name__ == "__main__":
    main()