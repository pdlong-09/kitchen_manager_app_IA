from __future__ import annotations
import sys
from pathlib import Path
from panda3d.core import Texture
from translations_items import ITEM_NAMES_VI, ITEM_NOTES_VI

LANGUAGES = ("en", "vi")

_state = {"lang": "en", "font": None, "font_ok": False, "font_path": None}

def get_language() -> str:
    return _state["lang"]

def set_language(code: str) -> None:
    if code in LANGUAGES:
        _state["lang"] = code

def toggle_language() -> str:
    set_language("vi" if _state["lang"] == "en" else "en")
    return _state["lang"]

def is_vietnamese() -> bool:
    return _state["lang"] == "vi"

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Verdana.ttf",
    "/System/Library/Fonts/Supplemental/Tahoma.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
]
PROBE_CHARACTERS = "ủạếữợằ"

def _font_has_vietnamese(font) -> bool:
    getter = getattr(font, "getGlyph", None)
    if getter is None:
        return True
    for character in PROBE_CHARACTERS:
        try:
            result = getter(ord(character))
        except Exception:
            return True
        if isinstance(result, tuple):
            ok, glyph = (result + (None,))[:2]
            if not ok or glyph is None:
                return False
        elif result is None:
            return False
    return True

def load_font(loader, extra_paths=()):
    if _state["font"] is not None or _state["font_ok"]:
        return _state["font"]
    candidates = list(extra_paths) + FONT_CANDIDATES
    for path in candidates:
        if not Path(path).is_file():
            continue
        try:
            font = loader.loadFont(path)
        except Exception:
            continue
        if font is None or not font.isValid():
            continue
        # has to be set before any glyph is made, so before the check below
        font.setPixelsPerUnit(80)
        font.setMinfilter(Texture.FTLinearMipmapLinear)
        if not _font_has_vietnamese(font):
            continue
        _state["font"] = font
        _state["font_ok"] = True
        _state["font_path"] = path
        return font
    print("[i18n] no vietnamese font found, staying in english. searched:\n  " + "\n  ".join(candidates), file=sys.stderr)
    _state["font_ok"] = False
    return None

def font_available() -> bool:
    return bool(_state["font_ok"])

def get_font():
    return _state["font"]

def font_path():
    return _state["font_path"]

UI = {
    # shell
    "app.title": ("Kitchen", "Nhà bếp"),
    "action.search": ("Search", "Tìm kiếm"),
    "lang.switch_to_vi": ("Tiếng Việt", "Tiếng Việt"),
    "lang.switch_to_en": ("English", "English"),
    "lang.unavailable": ("Vietnamese needs a system font that was not found.", "Vietnamese needs a system font that was not found."),
    # nav keys stay english, only the text changes
    "nav.To Do List": ("To Do List", "Việc cần làm"),
    "nav.Map": ("Map", "Sơ đồ"),
    "nav.Inventory": ("Inventory", "Kho"),
    "nav.Add Items": ("Add Items", "Thêm đồ"),
    # map page
    "map.heading": ("Location", "Vị trí"),
    "map.none_selected": ("None selected", "Chưa chọn"),
    "map.hint": ("Select a compartment or search for one.", "Chọn một ngăn tủ hoặc tìm kiếm."),
    "map.stored_here": ("Stored here", "Cất ở đây"),
    "map.no_items_yet": ("No items yet", "Chưa có đồ"),
    "map.no_items_here": ("No items stored here", "Không có đồ ở đây"),
    "map.more": ("+{n} more (see Inventory)", "+{n} đồ nữa (xem Kho)"),
    "map.group": ("Group {group}", "Nhóm {group}"),
    "map.top_view": ("Top view", "Nhìn từ trên"),
    "map.reset": ("Reset", "Đặt lại"),
    "map.controls": ("Rotate: left-drag\nPan: right-drag\nZoom: wheel", "Xoay: kéo chuột trái\nDi chuyển: kéo chuột phải\nPhóng to: lăn chuột"),
    # to do page
    "todo.title": ("To Do", "Việc cần làm"),
    "todo.subtitle": ("Items that need attention.", "Những món cần chú ý."),
    "todo.empty": ("Nothing to do yet.", "Chưa có việc gì."),
    "todo.expired": ("{name}: expired", "{name}: đã hết hạn"),
    "todo.out_of_stock": ("{name}: out of stock", "{name}: đã hết"),
    "todo.low_stock": ("{name}: low stock ({qty} {unit})", "{name}: sắp hết ({qty} {unit})"),
    "todo.restock": ("{name}: restock in {days} day(s)", "{name}: mua thêm sau {days} ngày"),
    # inventory page
    "inv.title": ("Inventory", "Kho"),
    "inv.subtitle": ("Select an item to view or update it.", "Chọn một món để xem hoặc cập nhật."),
    "inv.empty": ("No items yet.", "Chưa có món nào."),
    "inv.no_selection": ("No item selected", "Chưa chọn món nào"),
    "inv.use_one": ("Use 1", "Dùng 1"),
    "inv.add_one": ("Add 1", "Thêm 1"),
    "inv.view_on_map": ("View on map", "Xem trên sơ đồ"),
    "inv.edit": ("Edit", "Sửa"),
    "inv.delete": ("Delete", "Xoá"),
    "inv.location": ("Location {code}", "Vị trí {code}"),
    "inv.expiry": ("Expiry: {value}", "Hạn dùng: {value}"),
    "inv.low_stock": ("Low stock: {value}", "Mức sắp hết: {value}"),
    "inv.restock": ("Restock: {value}", "Mua thêm: {value}"),
    "inv.not_set": ("Not set", "Chưa đặt"),
    # add page
    "add.title": ("Add Item", "Thêm món"),
    "add.subtitle": ("Store a new item in the CSV.", "Lưu một món mới vào file CSV."),
    "add.hint": ("Dates use YYYY-MM-DD. Type should be Food, Supply, or Equipment.", "Ngày theo dạng YYYY-MM-DD. Loại nên là Thực phẩm, Vật dụng hoặc Thiết bị."),
    "add.title_edit": ("Edit Item", "Sửa món"),
    "add.subtitle_edit": ("Editing item #{id}. Save to overwrite it.", "Đang sửa món #{id}. Nhấn Cập nhật để ghi đè."),
    "add.save": ("Save", "Lưu"),
    "add.update": ("Update", "Cập nhật"),
    "add.cancel": ("Cancel edit", "Huỷ sửa"),
    "add.clear": ("Clear", "Xoá trắng"),
    # add page field labels
    "field.name": ("Name", "Tên"),
    "field.category": ("Category", "Danh mục"),
    "field.quantity": ("Quantity", "Số lượng"),
    "field.unit": ("Unit", "Đơn vị"),
    "field.item_type": ("Type", "Loại"),
    "field.location_code": ("Location", "Vị trí"),
    "field.low_stock_level": ("Low-stock level", "Mức sắp hết"),
    "field.expiry_date": ("Expiry date", "Hạn dùng"),
    "field.restock_date": ("Restock date", "Ngày mua thêm"),
    "field.notes": ("Notes", "Ghi chú"),
    # feedback / validation
    "msg.search_prompt": ("Enter an item name, category, or location code.", "Nhập tên món, danh mục hoặc mã vị trí."),
    "msg.filtered": ('Inventory filtered by "{text}".', 'Đã lọc kho theo "{text}".'),
    "msg.no_result": ('No result found for "{text}".', 'Không tìm thấy kết quả cho "{text}".'),
    "msg.showing": ("Showing {code}.", "Đang hiển thị {code}."),
    "msg.deleted": ("Deleted {name}.", "Đã xoá {name}."),
    "msg.saved": ("Saved {name}.", "Đã lưu {name}."),
    "msg.updated": ("Updated {name}.", "Đã cập nhật {name}."),
    "msg.missing_item": ("That item no longer exists.", "Món này không còn tồn tại."),
    "msg.edit_cancelled": ("Edit cancelled.", "Đã huỷ sửa."),
    "msg.required": ("Name, category, quantity, and unit are required.", "Tên, danh mục, số lượng và đơn vị là bắt buộc."),
    "msg.numbers": ("Quantity and low-stock level must be numbers.", "Số lượng và mức sắp hết phải là số."),
    "msg.negative": ("Quantities cannot be negative.", "Số lượng không được âm."),
    "msg.date_format": ("{label} must use YYYY-MM-DD.", "{label} phải theo dạng YYYY-MM-DD."),
    "msg.bad_location": ("Choose a valid location.", "Hãy chọn một vị trí hợp lệ."),
}

def t(key: str, **fmt) -> str:
    pair = UI.get(key)
    if pair is None:
        return key
    text = pair[1] if _state["lang"] == "vi" else pair[0]
    return text.format(**fmt) if fmt else text

LOCATION_NAMES = {
    "Upper cabinet and shelf": "Tủ trên và kệ mở",
    "Top drawer": "Ngăn kéo trên",
    "Bottom drawer": "Ngăn kéo dưới",
    "Base cabinet": "Tủ dưới",
    "Glass wall cabinet": "Tủ treo cửa kính",
    "Wall cabinet": "Tủ treo tường",
    "Upper pantry cabinet": "Tủ đồ khô phía trên",
    "Glass pantry cabinet": "Tủ đồ khô cửa kính",
    "Left pantry column": "Tủ đồ khô cột trái",
    "Right pantry column": "Tủ đồ khô cột phải",
    "Refrigerator doors": "Cánh tủ lạnh",
    "Fridge drawer": "Ngăn mát tủ lạnh",
    "Freezer drawer": "Ngăn đá tủ lạnh",
    "Wide island drawer": "Ngăn kéo rộng bàn đảo",
    "Island cabinet": "Tủ bàn đảo",
    "Island top drawer": "Ngăn kéo trên bàn đảo",
    "Island double cabinet": "Tủ đôi bàn đảo",
    "Sink-wall countertop": "Mặt bàn cạnh bồn rửa",
    "Top-wall countertop": "Mặt bàn tường trên",
    "Island countertop": "Mặt bàn đảo",
}

COMPARTMENT_TYPES = {
    "Combined Storage": "Khoang kết hợp",
    "Drawer": "Ngăn kéo",
    "Cabinet": "Tủ",
    "Glass": "Tủ kính",
    "Fridge Double": "Tủ lạnh hai cánh",
    "Countertop": "Mặt bàn bếp",
    "Open Shelf": "Kệ mở",
    "Appliance": "Thiết bị",
}

ITEM_TYPES = {
    "Alcohol": "Rượu",
    "Appliance": "Thiết bị",
    "Cleaning": "Vệ sinh",
    "Cookware": "Nồi chảo",
    "Drink": "Đồ uống",
    "Food": "Thực phẩm",
    "Glassware": "Đồ thuỷ tinh",
    "Household": "Đồ gia dụng",
    "Storage": "Đồ chứa",
    "Supplement": "Thực phẩm bổ sung",
    "Tableware": "Bát đĩa",
    "Utensil": "Dụng cụ",
}

UNITS = {
    "bag": "túi",
    "bottle": "chai",
    "box": "hộp",
    "bundle": "bó",
    "can": "lon",
    "carton": "hộp giấy",
    "jar": "lọ",
    "pack": "gói",
    "pair": "đôi",
    "pcs": "cái",
    "roll": "cuộn",
    "set": "bộ",
    "tin": "hộp thiếc",
    "tray": "khay",
    "tub": "hũ",
    "tube": "tuýp",
}

CATEGORIES = {
    "Bags": "Túi",
    "Chopping Boards": "Thớt",
    "Cleaning Supplies": "Đồ vệ sinh",
    "Condiment": "Gia vị",
    "Containers": "Hộp đựng",
    "Cooking Tools": "Dụng cụ nấu ăn",
    "Cutlery": "Dao thìa dĩa",
    "Dairy & Eggs": "Sữa và trứng",
    "Disposables": "Đồ dùng một lần",
    "Drinkware": "Ly cốc",
    "Dry Goods": "Đồ khô",
    "Fixtures": "Phụ kiện tủ",
    "Food Wrap": "Màng bọc thực phẩm",
    "Fresh Noodles": "Bún phở tươi",
    "Frozen": "Đồ đông lạnh",
    "Gifts": "Quà tặng",
    "Knives": "Dao",
    "Large Appliance": "Thiết bị lớn",
    "Leftovers": "Đồ ăn thừa",
    "Lids": "Vung nắp",
    "Measuring": "Dụng cụ đo",
    "Meat & Seafood": "Thịt và hải sản",
    "Mixing Bowls": "Tô trộn",
    "Paper Goods": "Đồ giấy",
    "Plates & Bowls": "Bát đĩa",
    "Pots & Pans": "Nồi chảo",
    "Produce": "Rau củ quả",
    "Protein Powder": "Bột protein",
    "Sake": "Rượu sake",
    "Serving Ware": "Đồ bày món",
    "Skincare": "Chăm sóc da",
    "Small Appliance": "Thiết bị nhỏ",
    "Snacks": "Đồ ăn vặt",
    "Soft Drinks": "Nước ngọt",
    "Steamers": "Xửng hấp",
    "Storage": "Đồ chứa",
    "Strainers": "Rổ rá",
    "Tea & Coffee": "Trà và cà phê",
    "Tea & Coffee Ware": "Ấm chén",
    "Vitamins": "Vitamin",
    "Waste": "Rác",
    "Water": "Nước",
    "Whisky": "Rượu whisky",
}

ITEM_NAMES = ITEM_NAMES_VI
ITEM_NOTES = ITEM_NOTES_VI

def _lookup(table: dict, value: str) -> str:
    if _state["lang"] != "vi" or not value:
        return value
    return table.get(value, value)

def tr_name(value: str) -> str:
    return _lookup(ITEM_NAMES, value)

def tr_category(value: str) -> str:
    return _lookup(CATEGORIES, value)

def tr_type(value: str) -> str:
    return _lookup(ITEM_TYPES, value)

def tr_unit(value: str) -> str:
    return _lookup(UNITS, value)

def tr_notes(value: str) -> str:
    return _lookup(ITEM_NOTES, value)

def tr_location_name(value: str) -> str:
    return _lookup(LOCATION_NAMES, value)

def tr_compartment_type(value: str) -> str:
    return _lookup(COMPARTMENT_TYPES, value)

def _reverse(table: dict) -> dict:
    return {vi.casefold(): en for en, vi in table.items()}

def canonical_type(value: str) -> str:
    return _reverse(ITEM_TYPES).get(value.strip().casefold(), value)

def canonical_category(value: str) -> str:
    return _reverse(CATEGORIES).get(value.strip().casefold(), value)

def canonical_unit(value: str) -> str:
    return _reverse(UNITS).get(value.strip().casefold(), value)
