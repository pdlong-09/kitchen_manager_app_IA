from __future__ import annotations
from pathlib import Path
from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton, DirectEntry, DirectFrame, DirectLabel
from panda3d.core import TextNode
import i18n

BG = (0.045, 0.052, 0.064, 1)
SURFACE = (0.065, 0.075, 0.090, 1)
SURFACE_LIGHT = (0.085, 0.098, 0.118, 1)
BORDER = (0.14, 0.16, 0.20, 1)
TEXT = (0.94, 0.95, 0.97, 1)
MUTED = (0.56, 0.61, 0.69, 1)
ACCENT = (0.33, 0.64, 0.96, 1)
DANGER = (0.88, 0.35, 0.38, 1)
TRANSPARENT = (0, 0, 0, 0)
ROWS = 8

class AppUI:
    def __init__(self, base, callbacks, location_codes):
        self.base = base
        self.callbacks = callbacks
        self.location_codes = sorted(location_codes)
        self.current_page = "Map"
        self.selected_item_id = None
        self.editing_item_id = None  # None = adding a new item
        self.inventory_page_index = 0
        self.todo_page_index = 0
        self.inventory_items = []
        self.todo_items = []
        self.translatable = []  # (widget, key) pairs that get re-labelled when the language changes
        self.font = i18n.load_font(base.loader, extra_paths=(str(Path(__file__).resolve().parent / "font.ttf"),))
        self.build_shell()
        self.build_map_page()
        self.build_todo_page()
        self.build_inventory_page()
        self.build_add_page()
        self.show_page("Map")

    def frame(self, size, color=BG, parent=None, pos=(0, 0, 0)):
        return DirectFrame(parent=parent, frameSize=size, frameColor=color, relief=DGG.FLAT, borderWidth=(0, 0), pos=pos)

    def label(self, parent, text="", pos=(0, 0, 0), scale=0.04, color=TEXT, align=TextNode.ALeft, wordwrap=None, key=None):
        if key is not None:
            text = i18n.t(key)
        options = {"parent": parent, "text": text, "text_scale": scale, "text_fg": color, "text_align": align,
                   "frameColor": TRANSPARENT, "relief": None, "pos": pos}
        if wordwrap is not None:
            options["text_wordwrap"] = wordwrap
        if self.font is not None:
            options["text_font"] = self.font
        widget = DirectLabel(**options)
        if key is not None:
            self.translatable.append((widget, key))
        return widget

    def button(self, parent, text, pos, command, extra_args=None, size=(-0.18, 0.18, -0.052, 0.052), color=SURFACE_LIGHT,
               text_color=TEXT, scale=0.037, align=TextNode.ACenter, key=None):
        if key is not None:
            text = i18n.t(key)
        if color == TRANSPARENT:
            hover, press = (1, 1, 1, 0.06), (1, 1, 1, 0.10)
        else:
            hover = tuple(min(1, c * 1.18) for c in color[:3]) + (color[3],)
            press = tuple(c * 0.85 for c in color[:3]) + (color[3],)
        options = {"parent": parent, "text": text, "text_scale": scale, "text_fg": text_color, "text_align": align,
                   "frameSize": size, "frameColor": (color, press, hover, color), "relief": DGG.FLAT, "borderWidth": (0, 0),
                   "rolloverSound": None, "clickSound": None, "pos": pos, "command": command, "extraArgs": extra_args or []}
        if self.font is not None:
            options["text_font"] = self.font
        widget = DirectButton(**options)
        if key is not None:
            self.translatable.append((widget, key))
        return widget

    def entry(self, parent, pos, width=10, initial_text=""):
        options = {"parent": parent, "initialText": initial_text, "scale": 0.040, "width": width, "frameColor": SURFACE_LIGHT,
                   "text_fg": TEXT, "cursorKeys": 1, "relief": DGG.FLAT, "borderWidth": (0, 0), "pos": pos}
        if self.font is not None:
            options["text_font"] = self.font
        return DirectEntry(**options)

    def divider(self, parent, x0, x1, z):
        return self.frame((x0, x1, -0.002, 0.002), BORDER, parent=parent, pos=(0, 0, z))

    def page_header(self, title_key, subtitle_key):
        page = self.frame((-1.72, 1.72, -0.77, 0.79), BG)
        title = self.label(page, pos=(-1.56, 0, 0.65), scale=0.052, key=title_key)
        subtitle = self.label(page, pos=(-1.56, 0, 0.55), scale=0.032, color=MUTED, key=subtitle_key)
        self.divider(page, -1.56, 1.56, 0.45)
        return page, title, subtitle

    def make_rows(self, parent, x, half_width, text_x, top_z, command, line_x0, line_x1):
        # 8 clickable rows for a list page, the text is filled in later
        rows = []
        for index in range(ROWS):
            z = top_z - index * 0.105
            row = self.button(parent, "", (x, 0, z), command, size=(-half_width, half_width, -0.045, 0.045), color=TRANSPARENT,
                              scale=0.035, align=TextNode.ALeft)
            row["text_pos"] = (text_x, -0.011)
            row.hide()
            rows.append(row)
            if index < ROWS - 1:
                self.divider(parent, line_x0, line_x1, z - 0.054)
        return rows

    def make_pager(self, parent, text_x, prev_x, next_x, command):
        text = self.label(parent, "", (text_x, 0, -0.63), scale=0.029, color=MUTED, align=TextNode.ARight)
        for symbol, x, step in (("‹", prev_x, -1), ("›", next_x, 1)):
            self.button(parent, symbol, (x, 0, -0.64), command, extra_args=[step], size=(-0.055, 0.055, -0.042, 0.042),
                        color=TRANSPARENT, text_color=MUTED, scale=0.050)
        return text

    def build_shell(self):
        self.top_bar = self.frame((-1.78, 1.78, -0.09, 0.09), (0.035, 0.041, 0.050, 1), pos=(0, 0, 0.91))
        self.label(self.top_bar, pos=(-1.63, 0, -0.012), scale=0.050, key="app.title")
        self.search_entry = self.entry(self.top_bar, (0.38, 0, -0.022), width=9.5)
        self.search_entry["command"] = self.callbacks["search"]
        self.button(self.top_bar, "", (1.03, 0, 0), lambda: self.callbacks["search"](self.search_entry.get()),
                    size=(-0.16, 0.16, -0.048, 0.048), color=ACCENT, key="action.search")
        self.language_button = self.button(self.top_bar, self.language_caption(), (1.47, 0, 0), self.toggle_language,
                                           size=(-0.19, 0.19, -0.048, 0.048), text_color=TEXT if i18n.font_available() else MUTED, scale=0.034)
        self.feedback = self.label(None, "", (-1.64, 0, -0.80), scale=0.031, color=MUTED)
        self.bottom_bar = self.frame((-1.78, 1.78, -0.085, 0.085), (0.035, 0.041, 0.050, 1), pos=(0, 0, -0.915))
        self.nav_buttons = {}
        self.nav_lines = {}
        for page, x in zip(["To Do List", "Map", "Inventory", "Add Items"], (-1.18, -0.39, 0.40, 1.19)):
            self.nav_buttons[page] = self.button(self.bottom_bar, i18n.t("nav." + page), (x, 0, 0.01), self.show_page, extra_args=[page],
                                                 size=(-0.28, 0.28, -0.055, 0.055), color=TRANSPARENT, text_color=MUTED, scale=0.039)
            self.nav_lines[page] = self.frame((-0.22, 0.22, -0.004, 0.004), ACCENT, parent=self.bottom_bar, pos=(x, 0, -0.064))
            self.nav_lines[page].hide()

    def build_map_page(self):
        self.map_page = self.frame((0.97, 1.76, -0.77, 0.79), (0.035, 0.041, 0.050, 0.97))
        self.label(self.map_page, pos=(1.05, 0, 0.66), scale=0.043, key="map.heading")
        self.map_title = self.label(self.map_page, i18n.t("map.none_selected"), (1.05, 0, 0.54), scale=0.037, wordwrap=16)
        self.map_details = self.label(self.map_page, i18n.t("map.hint"), (1.05, 0, 0.39), scale=0.031, color=MUTED, wordwrap=18)
        self.divider(self.map_page, 1.05, 1.67, 0.25)
        self.label(self.map_page, pos=(1.05, 0, 0.17), scale=0.036, key="map.stored_here")
        self.map_items = self.label(self.map_page, i18n.t("map.no_items_yet"), (1.05, 0, 0.06), scale=0.031, color=MUTED, wordwrap=18)
        self.button(self.map_page, "", (1.18, 0, -0.55), self.callbacks["top_view"], size=(-0.17, 0.17, -0.047, 0.047), key="map.top_view")
        self.button(self.map_page, "", (1.54, 0, -0.55), self.callbacks["reset_view"], size=(-0.14, 0.14, -0.047, 0.047), key="map.reset")
        self.label(self.map_page, pos=(1.05, 0, -0.66), scale=0.029, color=MUTED, key="map.controls")

    def build_todo_page(self):
        self.todo_page, _, _ = self.page_header("todo.title", "todo.subtitle")
        self.todo_rows = self.make_rows(self.todo_page, 0, 1.54, -1.47, 0.33, lambda: None, -1.54, 1.54)
        self.todo_empty = self.label(self.todo_page, pos=(0, 0, 0.05), scale=0.040, color=MUTED, align=TextNode.ACenter, key="todo.empty")
        self.todo_page_text = self.make_pager(self.todo_page, 1.10, 1.34, 1.53, self.change_todo_page)

    def build_inventory_page(self):
        self.inventory_page, _, _ = self.page_header("inv.title", "inv.subtitle")
        page = self.inventory_page
        # left side: item list
        self.list_panel = self.frame((-1.56, -0.28, -0.57, 0.40), TRANSPARENT, parent=page)
        self.inventory_rows = self.make_rows(page, -0.92, 0.62, -0.57, 0.31, self.callbacks["select_item"], -1.54, -0.31)
        self.inventory_empty = self.label(page, i18n.t("inv.empty"), (-0.92, 0, 0.05), scale=0.039, color=MUTED, align=TextNode.ACenter)
        self.inventory_page_text = self.make_pager(page, -0.60, -0.46, -0.29, self.change_inventory_page)
        self.frame((-0.002, 0.002, -0.57, 0.40), BORDER, parent=page, pos=(-0.12, 0, 0))
        # right side: selected item
        self.inventory_title = self.label(page, i18n.t("inv.no_selection"), (0.05, 0, 0.33), scale=0.045)
        self.inventory_details = self.label(page, "", (0.05, 0, 0.19), scale=0.033, color=MUTED, wordwrap=24)
        actions = [(0.11, 0.13, "change_quantity", [-1], "inv.use_one"), (0.40, 0.13, "change_quantity", [1], "inv.add_one"),
                   (0.68, 0.12, "edit_item", None, "inv.edit"), (1.03, 0.20, "view_item_map", None, "inv.view_on_map")]
        for x, half_width, callback, args, key in actions:
            self.button(page, "", (x, 0, -0.44), self.callbacks[callback], extra_args=args, size=(-half_width, half_width, -0.047, 0.047), key=key)
        self.button(page, "", (1.44, 0, -0.44), self.callbacks["delete_item"], size=(-0.13, 0.13, -0.047, 0.047), color=TRANSPARENT,
                    text_color=DANGER, key="inv.delete")

    def build_add_page(self):
        self.add_page, self.add_title, self.add_subtitle = self.page_header("add.title", "add.subtitle")
        self.add_entries = {}
        fields = [("name", -1.35, 0.27, ""), ("category", -1.35, 0.02, ""), ("quantity", -1.35, -0.23, ""), ("unit", -1.35, -0.48, ""),
                  ("item_type", -0.28, 0.27, "Food"), ("location_code", -0.28, 0.02, "A1"), ("low_stock_level", -0.28, -0.23, "0"),
                  ("expiry_date", -0.28, -0.48, ""), ("restock_date", 0.79, 0.27, ""), ("notes", 0.79, 0.02, "")]
        for key, x, z, default in fields:
            self.label(self.add_page, pos=(x, 0, z + 0.075), scale=0.031, color=MUTED, key="field." + key)
            self.add_entries[key] = self.entry(self.add_page, (x, 0, z), width=11, initial_text=default)
        self.label(self.add_page, pos=(-1.35, 0, -0.62), scale=0.029, color=MUTED, key="add.hint")
        self.add_feedback = self.label(self.add_page, "", (-1.35, 0, -0.70), scale=0.031, color=MUTED)
        self.save_button = self.button(self.add_page, "", (1.12, 0, -0.63), self.save_item, size=(-0.16, 0.16, -0.052, 0.052),
                                       color=ACCENT, key="add.save")
        self.clear_button = self.button(self.add_page, "", (1.48, 0, -0.63), self.clear_add_form, size=(-0.16, 0.16, -0.052, 0.052),
                                        color=TRANSPARENT, text_color=MUTED, key="add.clear")

    def language_caption(self):
        # button shows the language you would switch to
        return i18n.t("lang.switch_to_en" if i18n.is_vietnamese() else "lang.switch_to_vi")

    def toggle_language(self):
        if not i18n.font_available() and not i18n.is_vietnamese():
            self.set_feedback(i18n.t("lang.unavailable"))
            return
        i18n.toggle_language()
        self.apply_language()
        self.callbacks["language_changed"]()

    def apply_language(self):
        for widget, key in self.translatable:
            widget["text"] = i18n.t(key)
        for page, button in self.nav_buttons.items():
            button["text"] = i18n.t("nav." + page)
        self.language_button["text"] = self.language_caption()
        self.inventory_empty["text"] = i18n.t("inv.empty")
        self.todo_empty["text"] = i18n.t("todo.empty")
        self.map_title["text"] = i18n.t("map.none_selected")
        self.map_details["text"] = i18n.t("map.hint")
        self.map_items["text"] = i18n.t("map.no_items_yet")
        self.inventory_title["text"] = i18n.t("inv.no_selection")
        self.inventory_details["text"] = ""
        self.refresh_add_mode()

    def show_page(self, page):
        self.current_page = page
        pages = {"Map": self.map_page, "To Do List": self.todo_page, "Inventory": self.inventory_page, "Add Items": self.add_page}
        for name, frame in pages.items():
            if name == page:
                frame.show()
                self.nav_lines[name].show()
            else:
                frame.hide()
                self.nav_lines[name].hide()
            self.nav_buttons[name]["text_fg"] = ACCENT if name == page else MUTED
        self.callbacks["page_changed"](page)

    def set_feedback(self, text):
        self.feedback["text"] = text

    def set_map_location(self, compartment, items):
        if compartment is None:
            self.map_title["text"] = i18n.t("map.none_selected")
            self.map_details["text"] = i18n.t("map.hint")
            self.map_items["text"] = i18n.t("map.no_items_yet")
            return
        display = compartment.display or compartment.code
        self.map_title["text"] = f"{display} · {i18n.tr_location_name(compartment.name)}"
        compartment_type = compartment.compartment_type.replace("_", " ").title()
        self.map_details["text"] = i18n.t("map.group", group=compartment.group) + "\n" + i18n.tr_compartment_type(compartment_type)
        if not items:
            self.map_items["text"] = i18n.t("map.no_items_here")
            return
        lines = [f"{i18n.tr_name(item.name)}  ·  {item.quantity:g} {i18n.tr_unit(item.unit)}" for item in items[:9]]
        if len(items) > 9:
            lines.append(i18n.t("map.more", n=len(items) - 9))
        self.map_items["text"] = "\n".join(lines)

    @staticmethod
    def page_count(items):
        return max(1, (len(items) + ROWS - 1) // ROWS)

    def show_rows(self, rows, empty_label, items, index, page_text):
        # hides all rows and returns (row, item) pairs for the current page
        for row in rows:
            row.hide()
        visible = items[index * ROWS:(index + 1) * ROWS]
        if visible:
            empty_label.hide()
        else:
            empty_label.show()
        page_text["text"] = f"{index + 1} / {self.page_count(items)}"
        return list(zip(rows, visible))

    def refresh_todo(self, alerts):
        self.todo_items = list(alerts)
        self.todo_page_index = 0
        self.render_todo_page()

    def render_todo_page(self):
        for row, alert in self.show_rows(self.todo_rows, self.todo_empty, self.todo_items, self.todo_page_index, self.todo_page_text):
            row["text"] = alert
            row.show()

    def change_todo_page(self, amount):
        self.todo_page_index = max(0, min(self.page_count(self.todo_items) - 1, self.todo_page_index + amount))
        self.render_todo_page()

    def refresh_inventory(self, items):
        self.inventory_items = list(items)
        self.inventory_page_index = 0
        self.render_inventory_page()

    def render_inventory_page(self):
        shown = self.show_rows(self.inventory_rows, self.inventory_empty, self.inventory_items, self.inventory_page_index, self.inventory_page_text)
        if not shown:
            self.set_inventory_item(None)
        for row, item in shown:
            row["text"] = f"{i18n.tr_name(item.name)}   {item.quantity:g} {i18n.tr_unit(item.unit)}   ·   {item.location_code}"
            row["extraArgs"] = [item.item_id]
            row.show()
        self.update_row_highlight()

    def change_inventory_page(self, amount):
        self.inventory_page_index = max(0, min(self.page_count(self.inventory_items) - 1, self.inventory_page_index + amount))
        self.render_inventory_page()

    def update_row_highlight(self):
        for row in self.inventory_rows:
            selected = self.selected_item_id is not None and row["extraArgs"] == [self.selected_item_id]
            base = SURFACE_LIGHT if selected else TRANSPARENT
            hover = SURFACE_LIGHT if selected else (1, 1, 1, 0.06)
            row["frameColor"] = (base, base, hover, base)

    def set_inventory_item(self, item):
        if item is None:
            self.selected_item_id = None
            self.inventory_title["text"] = i18n.t("inv.no_selection")
            self.inventory_details["text"] = ""
            self.update_row_highlight()
            return
        not_set = i18n.t("inv.not_set")
        self.selected_item_id = item.item_id
        self.inventory_title["text"] = i18n.tr_name(item.name)
        lines = [f"{i18n.tr_type(item.item_type)} · {i18n.tr_category(item.category)}", "",
                 f"{item.quantity:g} {i18n.tr_unit(item.unit)}", i18n.t("inv.location", code=item.location_code), "",
                 i18n.t("inv.expiry", value=item.expiry_date or not_set), i18n.t("inv.low_stock", value=f"{item.low_stock_level:g}"),
                 i18n.t("inv.restock", value=item.restock_date or not_set), i18n.tr_notes(item.notes or "")]
        self.inventory_details["text"] = "\n".join(lines)
        self.update_row_highlight()

    def save_item(self):
        data = {key: entry.get().strip() for key, entry in self.add_entries.items()}
        # anything typed in vietnamese gets saved back in english
        data["item_type"] = i18n.canonical_type(data["item_type"]).title()
        data["category"] = i18n.canonical_category(data["category"])
        data["unit"] = i18n.canonical_unit(data["unit"])
        data["location_code"] = data["location_code"].upper()
        if self.editing_item_id is None:
            success, message = self.callbacks["add_item"](data)
        else:
            success, message = self.callbacks["update_item"](self.editing_item_id, data)
        self.add_feedback["text"] = message
        self.add_feedback["text_fg"] = ACCENT if success else DANGER
        if success:
            self.clear_add_form(clear_feedback=False)

    def clear_add_form(self, clear_feedback=True):
        was_editing = self.editing_item_id is not None
        defaults = {"item_type": "Food", "location_code": "A1", "low_stock_level": "0"}
        for key, entry in self.add_entries.items():
            entry.enterText(defaults.get(key, ""))
        self.editing_item_id = None
        self.refresh_add_mode()
        if clear_feedback:
            self.add_feedback["text"] = ""
            if was_editing:
                self.set_feedback(i18n.t("msg.edit_cancelled"))

    def refresh_add_mode(self):
        if self.editing_item_id is not None:
            self.add_title["text"] = i18n.t("add.title_edit")
            self.add_subtitle["text"] = i18n.t("add.subtitle_edit", id=self.editing_item_id)
            self.save_button["text"] = i18n.t("add.update")
            self.clear_button["text"] = i18n.t("add.cancel")
        else:
            self.add_title["text"] = i18n.t("add.title")
            self.add_subtitle["text"] = i18n.t("add.subtitle")
            self.save_button["text"] = i18n.t("add.save")
            self.clear_button["text"] = i18n.t("add.clear")

    def begin_edit(self, item):
        self.editing_item_id = item.item_id
        values = {"name": item.name, "category": item.category, "quantity": f"{item.quantity:g}", "unit": item.unit,
                  "item_type": item.item_type, "location_code": item.location_code, "low_stock_level": f"{item.low_stock_level:g}",
                  "expiry_date": item.expiry_date, "restock_date": item.restock_date, "notes": item.notes}
        for key, entry in self.add_entries.items():
            entry.enterText(values.get(key, ""))
        self.add_feedback["text"] = ""
        self.refresh_add_mode()
        self.show_page("Add Items")
