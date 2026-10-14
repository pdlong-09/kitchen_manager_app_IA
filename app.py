from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from direct.showbase.ShowBase import ShowBase
from panda3d.core import AntialiasAttrib, loadPrcFileData

loadPrcFileData("", "window-title Kitchen Management System")
loadPrcFileData("", "win-size 1440 860")
loadPrcFileData("", "framebuffer-multisample 1")
loadPrcFileData("", "multisamples 4")
loadPrcFileData("", "audio-library-name null")

import i18n
from map_view import KitchenMapView
from store import SQLiteItemStore
from ui import AppUI

class KitchenManagerApp(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        self.render.setAntialias(AntialiasAttrib.MAuto)
        self.setBackgroundColor(0.09, 0.09, 0.11)
        project_root = Path(__file__).resolve().parent
        # items.csv only fills the db on first run, after that it is just a copy
        self.store = SQLiteItemStore(project_root / "kitchen.db", project_root / "items.csv")
        self.map_view = KitchenMapView(self, self.on_map_select)
        callbacks = {
            "page_changed": self.on_page_changed,
            "search": self.search,
            "top_view": self.map_view.top_view,
            "reset_view": self.map_view.reset_view,
            "select_item": self.select_item,
            "change_quantity": self.change_quantity,
            "view_item_map": self.view_item_map,
            "delete_item": self.delete_item,
            "add_item": self.add_item,
            "update_item": self.update_item,
            "edit_item": self.edit_item,
            "language_changed": self.on_language_changed,
        }
        self.ui = AppUI(self, callbacks, self.map_view.valid_codes)
        self.refresh_inventory()
        self.refresh_todo()
        self.accept("escape", self.userExit)

    def on_page_changed(self, page):
        if page == "Map":
            self.map_view.show()
        else:
            self.map_view.hide()
        if page == "Inventory":
            self.refresh_inventory(self.ui.search_entry.get())
        elif page == "To Do List":
            self.refresh_todo()

    def on_map_select(self, code):
        if code is None:
            self.ui.set_map_location(None, [])
            return
        location = self.map_view.by_code[code]
        items = self.store.get_items_at_location(code)
        self.ui.set_map_location(location, items)

    def search(self, text):
        text = text.strip()
        if not text:
            self.ui.set_feedback(i18n.t("msg.search_prompt"))
            return
        if self.ui.current_page == "Inventory":
            self.refresh_inventory(text)
            self.ui.set_feedback(i18n.t("msg.filtered", text=text))
            return
        code = self.store.find_location_for_search(text, self.map_view.valid_codes)
        if code is None or code not in self.map_view.valid_codes:
            self.ui.set_feedback(i18n.t("msg.no_result", text=text))
            return
        self.ui.show_page("Map")
        self.map_view.select(code, focus=True)
        self.ui.set_feedback(i18n.t("msg.showing", code=code))

    def refresh_inventory(self, search=""):
        self.ui.refresh_inventory(self.store.get_items(search))

    def select_item(self, item_id):
        self.ui.set_inventory_item(self.store.get_item(item_id))

    def selected_item(self):
        if self.ui.selected_item_id is None:
            return None
        return self.store.get_item(self.ui.selected_item_id)

    def change_quantity(self, amount):
        item = self.selected_item()
        if item is None:
            return
        self.store.update_quantity(item.item_id, item.quantity + amount)
        self.ui.set_inventory_item(self.store.get_item(item.item_id))
        self.refresh_inventory(self.ui.search_entry.get())
        self.refresh_todo()

    def view_item_map(self):
        item = self.selected_item()
        if item is None:
            return
        self.ui.show_page("Map")
        self.map_view.select(item.location_code, focus=True)

    def edit_item(self):
        item = self.selected_item()
        if item is not None:
            self.ui.begin_edit(item)

    def delete_item(self):
        item = self.selected_item()
        if item is None:
            return
        self.store.delete_item(item.item_id)
        self.ui.set_inventory_item(None)
        self.refresh_inventory(self.ui.search_entry.get())
        self.refresh_todo()
        self.ui.set_feedback(i18n.t("msg.deleted", name=i18n.tr_name(item.name)))

    def validate_item(self, data):
        # used by both add and update, returns (ok, message)
        required = ["name", "category", "quantity", "unit"]
        if any(not data[field] for field in required):
            return False, i18n.t("msg.required")
        try:
            quantity = float(data["quantity"])
            low_stock = float(data["low_stock_level"] or 0)
        except ValueError:
            return False, i18n.t("msg.numbers")
        if quantity < 0 or low_stock < 0:
            return False, i18n.t("msg.negative")
        for field in ("expiry_date", "restock_date"):
            value = data[field]
            if value:
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    label = i18n.t("field." + field)
                    return False, i18n.t("msg.date_format", label=label)
        data["location_code"] = data["location_code"].upper()
        if data["location_code"] not in self.map_view.valid_codes:
            return False, i18n.t("msg.bad_location")
        return True, ""

    def add_item(self, data):
        ok, message = self.validate_item(data)
        if not ok:
            return False, message
        self.store.add_item(data)
        self.refresh_inventory()
        self.refresh_todo()
        return True, i18n.t("msg.saved", name=data["name"])

    def update_item(self, item_id, data):
        ok, message = self.validate_item(data)
        if not ok:
            return False, message
        if self.store.update_item(item_id, data) is None:
            return False, i18n.t("msg.missing_item")
        self.refresh_inventory(self.ui.search_entry.get())
        self.refresh_todo()
        self.ui.set_inventory_item(self.store.get_item(item_id))
        return True, i18n.t("msg.updated", name=data["name"])

    def on_language_changed(self):
        # panels that show item data have to be rebuilt from the store
        self.refresh_inventory(self.ui.search_entry.get())
        self.refresh_todo()
        self.on_map_select(self.map_view.selected or None)
        if self.ui.selected_item_id is not None:
            self.ui.set_inventory_item(self.store.get_item(self.ui.selected_item_id))

    def refresh_todo(self):
        alerts = []
        today = date.today()
        for item in self.store.get_items():
            name = i18n.tr_name(item.name)
            if item.expiry_date:
                expiry = datetime.strptime(item.expiry_date, "%Y-%m-%d").date()
                if expiry < today:
                    alerts.append(i18n.t("todo.expired", name=name))
            if item.quantity <= 0:
                alerts.append(i18n.t("todo.out_of_stock", name=name))
            elif item.low_stock_level and item.quantity <= item.low_stock_level:
                unit = i18n.tr_unit(item.unit)
                alerts.append(i18n.t("todo.low_stock", name=name, qty=f"{item.quantity:g}", unit=unit))
            if item.restock_date:
                restock = datetime.strptime(item.restock_date, "%Y-%m-%d").date()
                days_left = (restock - today).days
                if 0 <= days_left <= 5:
                    alerts.append(i18n.t("todo.restock", name=name, days=days_left))
        self.ui.refresh_todo(alerts)

if __name__ == "__main__":
    KitchenManagerApp().run()
