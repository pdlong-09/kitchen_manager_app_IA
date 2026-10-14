from __future__ import annotations
import math
from dataclasses import dataclass
from panda3d.core import (BitMask32, CollisionBox, CollisionHandlerQueue, CollisionNode, CollisionRay, CollisionTraverser,
                          Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter,
                          OrthographicLens, Point3, TextNode, TransparencyAttrib, Vec3)

@dataclass(frozen=True)
class CabinetPart:
    part_id: str
    location_code: str | None
    group: str
    center: tuple
    size: tuple
    front_direction: str
    part_type: str
    aux: bool = False

@dataclass
class Location:
    code: str
    group: str
    center: tuple
    size: tuple
    front_direction: str
    compartment_type: str
    name: str
    display: str = ""

def make_part(part_id, location_code, group, part_type, x0, x1, y0, y1, z0, z1, front, aux=False):
    center = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    return CabinetPart(part_id, location_code, group, center, (x1 - x0, y1 - y0, z1 - z0), front, part_type, aux)

P = make_part

# one part = one door/drawer/shelf, parts with the same code open into the same space
PARTS = [
    P("C1", "C1", "C", "cabinet", 0.00, 0.35, 3.60, 4.05, 1.45, 2.25, "+x"),
    P("C2a", "C2", "C", "cabinet", 0.00, 0.60, 2.80, 3.30, 0.10, 0.90, "+x"),
    P("C2b", "C2", "C", "cabinet", 0.00, 0.60, 3.30, 3.80, 0.10, 0.90, "+x"),
    P("B1", "B1", "B", "glass", 0.00, 0.35, 1.38, 2.12, 1.45, 2.25, "+x"),
    P("B2", "B2", "B", "glass", 0.00, 0.35, 2.12, 2.86, 1.45, 2.25, "+x"),
    P("B3", "B3", "B", "glass", 0.00, 0.35, 2.86, 3.60, 1.45, 2.25, "+x"),
    P("A1a", "A1", "A", "cabinet", 0.00, 0.35, 0.40, 0.89, 1.85, 2.25, "+x"),
    P("A1b", "A1", "A", "cabinet", 0.00, 0.35, 0.89, 1.38, 1.85, 2.25, "+x"),
    P("A1c", "A1", "A", "open_shelf", 0.00, 0.35, 0.40, 1.38, 1.45, 1.85, "+x"),
    P("A2", "A2", "A", "drawer", 0.00, 0.60, 0.40, 1.10, 0.50, 0.90, "+x"),
    P("A3", "A3", "A", "drawer", 0.00, 0.60, 0.40, 1.10, 0.10, 0.50, "+x"),
    P("A4a", "A4", "A", "cabinet", 0.00, 0.60, 1.10, 1.65, 0.10, 0.90, "+x"),
    P("A4b", "A4", "A", "cabinet", 0.00, 0.60, 1.65, 2.20, 0.10, 0.90, "+x"),
    P("DW", None, "AUX", "appliance", 0.00, 0.60, 2.20, 2.80, 0.10, 0.90, "+x", aux=True),
    P("D1", "D1", "D", "cabinet", 0.35, 0.87, 4.05, 4.40, 1.45, 2.25, "-y"),
    P("D2a", "D2", "D", "cabinet", 0.87, 1.38, 4.05, 4.40, 1.45, 2.25, "-y"),
    P("D2b", "D2", "D", "cabinet", 1.38, 1.90, 4.05, 4.40, 1.45, 2.25, "-y"),
    P("D3", "D3", "D", "cabinet", 0.60, 1.25, 3.80, 4.40, 0.10, 0.90, "-y"),
    P("D4", "D4", "D", "drawer", 1.25, 1.90, 3.80, 4.40, 0.50, 0.90, "-y"),
    P("D5", "D5", "D", "drawer", 1.25, 1.90, 3.80, 4.40, 0.10, 0.50, "-y"),
    P("E1", "E1", "E", "cabinet", 2.000, 2.525, 3.70, 4.40, 1.55, 2.25, "-y"),
    P("E2a", "E2", "E", "glass", 2.525, 3.050, 3.70, 4.40, 1.55, 2.25, "-y"),
    P("E2b", "E2", "E", "glass", 3.050, 3.575, 3.70, 4.40, 1.55, 2.25, "-y"),
    P("E3", "E3", "E", "cabinet", 3.575, 4.100, 3.70, 4.40, 1.55, 2.25, "-y"),
    P("E4", "E4", "E", "cabinet", 2.00, 2.45, 3.70, 4.40, 0.10, 1.55, "-y"),
    P("E5", "E5", "E", "cabinet", 3.65, 4.10, 3.70, 4.40, 0.10, 1.55, "-y"),
    P("F1", "F1", "F", "fridge_double", 2.45, 3.65, 3.70, 4.40, 0.75, 1.55, "-y"),
    P("F2", "F2", "F", "drawer", 2.45, 3.05, 3.70, 4.40, 0.45, 0.75, "-y"),
    P("F3", "F3", "F", "drawer", 3.05, 3.65, 3.70, 4.40, 0.45, 0.75, "-y"),
    P("F4", "F4", "F", "drawer", 2.45, 3.05, 3.70, 4.40, 0.10, 0.45, "-y"),
    P("F5", "F5", "F", "drawer", 3.05, 3.65, 3.70, 4.40, 0.10, 0.45, "-y"),
    P("G1", "G1", "G", "drawer", 3.33, 4.03, 0.48, 1.34, 0.10, 0.45, "+y"),
    P("MW", None, "AUX", "appliance", 3.33, 4.03, 0.48, 1.34, 0.45, 0.85, "+y", aux=True),
    P("G2", "G2", "G", "cabinet", 2.93, 3.33, 0.48, 1.34, 0.10, 0.85, "+y"),
    P("G3", "G3", "G", "drawer", 2.13, 2.93, 0.48, 1.34, 0.60, 0.85, "+y"),
    P("G4_a", "G4", "G", "cabinet", 2.53, 2.93, 0.48, 1.34, 0.10, 0.60, "+y"),
    P("G4_b", "G4", "G", "cabinet", 2.13, 2.53, 0.48, 1.34, 0.10, 0.60, "+y"),
    P("G5", "G5", "G", "cabinet", 1.57, 2.13, 0.48, 1.34, 0.10, 0.85, "+y"),
    P("CT1", "CT1", "CT", "countertop", 0.00, 0.65, 0.35, 4.35, 0.90, 0.94, "+x"),
    P("CT2", "CT2", "CT", "countertop", 0.65, 1.95, 3.78, 4.40, 0.90, 0.94, "-y"),
    P("CT3", "CT3", "CT", "countertop", 1.50, 4.10, 0.40, 1.42, 0.85, 0.90, "+y"),
]

LOCATION_INFO = {
    "A1": ("Upper cabinet and shelf", "combined_storage"),
    "A2": ("Top drawer", "drawer"),
    "A3": ("Bottom drawer", "drawer"),
    "A4": ("Base cabinet", "cabinet"),
    "B1": ("Glass wall cabinet", "glass"),
    "B2": ("Glass wall cabinet", "glass"),
    "B3": ("Glass wall cabinet", "glass"),
    "C1": ("Wall cabinet", "cabinet"),
    "C2": ("Base cabinet", "cabinet"),
    "D1": ("Wall cabinet", "cabinet"),
    "D2": ("Wall cabinet", "cabinet"),
    "D3": ("Base cabinet", "cabinet"),
    "D4": ("Top drawer", "drawer"),
    "D5": ("Bottom drawer", "drawer"),
    "E1": ("Upper pantry cabinet", "cabinet"),
    "E2": ("Glass pantry cabinet", "glass"),
    "E3": ("Upper pantry cabinet", "cabinet"),
    "E4": ("Left pantry column", "cabinet"),
    "E5": ("Right pantry column", "cabinet"),
    "F1": ("Refrigerator doors", "fridge_double"),
    "F2": ("Fridge drawer", "drawer"),
    "F3": ("Fridge drawer", "drawer"),
    "F4": ("Freezer drawer", "drawer"),
    "F5": ("Freezer drawer", "drawer"),
    "G1": ("Wide island drawer", "drawer"),
    "G2": ("Island cabinet", "cabinet"),
    "G3": ("Island top drawer", "drawer"),
    "G4": ("Island double cabinet", "cabinet"),
    "G5": ("Island cabinet", "cabinet"),
    "CT1": ("Sink-wall countertop", "countertop"),
    "CT2": ("Top-wall countertop", "countertop"),
    "CT3": ("Island countertop", "countertop"),
}

GROUP_LABELS = {
    "C": (0.30, 3.90, 2.50),
    "B": (0.30, 2.50, 2.50),
    "A": (0.30, 0.90, 2.50),
    "D": (1.15, 4.10, 2.50),
    "E": (3.05, 4.05, 2.58),
    "F": (3.05, 3.42, 1.95),
    "G": (2.80, 1.58, 1.15),
}

STATIC_BOXES = [
    (0.04, 0.56, 0.46, 3.76, 0.00, 0.10, (0.10, 0.10, 0.11)),
    (0.66, 1.90, 3.86, 4.36, 0.00, 0.10, (0.10, 0.10, 0.11)),
    (2.02, 4.08, 3.76, 4.36, 0.00, 0.10, (0.10, 0.10, 0.11)),
    (1.63, 3.97, 0.54, 1.28, 0.00, 0.10, (0.10, 0.10, 0.11)),
    (0.00, 0.60, 3.80, 4.40, 1.45, 1.45, (0.10, 0.10, 0.11)),
    (0.00, 0.60, 3.80, 4.40, 0.00, 0.90, (0.10, 0.10, 0.11)),
    (0.045, 0.65, 4.35, 4.40, 0.90, 0.94, (0.14, 0.14, 0.15)),
    (0.00, 0.35, 4.05, 4.40, 1.45, 2.25, (0.10, 0.10, 0.11)),
    (1.57, 4.03, 0.44, 0.48, 0.10, 0.85, (0.40, 0.28, 0.18)),
    (0.000, 0.045, 0.35, 4.35, 0.94, 1.45, (0.11, 0.11, 0.12)),
    (0.045, 1.92, 4.355, 4.40, 0.94, 1.45, (0.11, 0.11, 0.12)),
    (0.14, 0.52, 1.15, 1.75, 0.941, 0.946, (0.33, 0.34, 0.36)),
    (0.14, 0.52, 2.50, 3.10, 0.941, 0.946, (0.33, 0.34, 0.36)),
    (2.20, 3.10, 0.60, 1.20, 0.901, 0.906, (0.05, 0.05, 0.06)),
]

GROUP_COLORS = {
    "A": (0.95, 0.47, 0.44),
    "B": (0.49, 0.80, 0.50),
    "C": (0.49, 0.71, 0.83),
    "D": (0.76, 0.44, 0.79),
    "E": (0.79, 0.58, 0.39),
    "F": (0.98, 0.60, 0.72),
    "G": (0.99, 0.85, 0.46),
}
CT_COLOR = (0.14, 0.14, 0.15)
FLOOR_COLOR = (0.17, 0.17, 0.18)
WALL_COLOR = (0.55, 0.53, 0.50)
HANDLE_COLOR = (0.82, 0.68, 0.40)
APPLIANCE_COLORS = {"DW": (0.62, 0.63, 0.65), "MW": (0.20, 0.20, 0.22)}
GLASS_COLOR = (0.15, 0.21, 0.21)

ROOM_CENTER = (2.20, 2.40, 1.05)
ROOM_SPAN = (4.60, 4.20, 2.35)

USABLE_WIDTH = 0.775
USABLE_HEIGHT = 0.780
PANEL_NDC = 0.225
VERT_NDC = 0.020
MARGIN = 1.06
FOCUS_HEADINGS = {"-y": 25, "+x": 55, "+y": 145, "-x": 215}
HOME_HEADING = 40
HOME_PITCH = -30

LIGHT = Vec3(-0.40, -0.55, 0.73).normalized()
HEADINGS = {"-y": 0, "+x": 90, "+y": 180, "-x": 270}
PANEL_T = 0.020
GAP = 0.008
DOOR_T = 0.022
PICK_MASK = BitMask32.bit(1)

def shade(normal):
    amount = Vec3(*normal).dot(LIGHT)
    return min(1.0, 0.58 + 0.42 * max(0.0, amount))

def box_faces(x0, x1, y0, y1, z0, z1):
    return [
        ((1, 0, 0), [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)]),
        ((-1, 0, 0), [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)]),
        ((0, 1, 0), [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)]),
        ((0, -1, 0), [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]),
        ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
        ((0, 0, -1), [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)]),
    ]

def add_box(parent, center, size, color, alpha=1.0, name="box"):
    cx, cy, cz = center
    sx, sy, sz = size
    faces = box_faces(cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2)
    vertex_data = GeomVertexData(name, GeomVertexFormat.getV3c4(), Geom.UHStatic)
    vertex_writer = GeomVertexWriter(vertex_data, "vertex")
    color_writer = GeomVertexWriter(vertex_data, "color")
    triangles = GeomTriangles(Geom.UHStatic)
    index = 0
    for normal, corners in faces:
        face_shade = shade(normal)
        face_color = (color[0] * face_shade, color[1] * face_shade, color[2] * face_shade, alpha)
        for corner in corners:
            vertex_writer.addData3(*corner)
            color_writer.addData4(*face_color)
        triangles.addVertices(index, index + 1, index + 2)
        triangles.addVertices(index, index + 2, index + 3)
        index += 4
    geometry = Geom(vertex_data)
    geometry.addPrimitive(triangles)
    node = GeomNode(name)
    node.addGeom(geometry)
    node_path = parent.attachNewNode(node)
    if alpha < 1.0:
        node_path.setTransparency(TransparencyAttrib.MAlpha)
    return node_path

def add_quad(parent, vertices, color, name):
    vertex_data = GeomVertexData(name, GeomVertexFormat.getV3c4(), Geom.UHStatic)
    vertex_writer = GeomVertexWriter(vertex_data, "vertex")
    color_writer = GeomVertexWriter(vertex_data, "color")
    triangles = GeomTriangles(Geom.UHStatic)
    for vertex in vertices:
        vertex_writer.addData3(*vertex)
        color_writer.addData4(*color, 1.0)
    triangles.addVertices(0, 1, 2)
    triangles.addVertices(0, 2, 3)
    geometry = Geom(vertex_data)
    geometry.addPrimitive(triangles)
    node = GeomNode(name)
    node.addGeom(geometry)
    return parent.attachNewNode(node)

def create_label(parent, text, position, scale, color=(1, 1, 1, 1)):
    text_node = TextNode("label-" + text)
    text_node.setText(text)
    text_node.setAlign(TextNode.ACenter)
    text_node.setTextColor(*color)
    text_node.setShadow(0.06, 0.06)
    text_node.setShadowColor(0, 0, 0, 1)
    label = parent.attachNewNode(text_node)
    label.setScale(scale)
    label.setPos(*position)
    label.setBillboardPointEye()
    return label

def local_size(compartment):
    sx, sy, sz = compartment.size
    if compartment.front_direction in ("+x", "-x"):
        return sy, sx, sz
    return sx, sy, sz

def create_carcass(parent, width, depth, height, color):
    t = PANEL_T
    add_box(parent, (-(width / 2 - t / 2), 0, 0), (t, depth, height), color)
    add_box(parent, (width / 2 - t / 2, 0, 0), (t, depth, height), color)
    add_box(parent, (0, 0, height / 2 - t / 2), (width - 2 * t, depth, t), color)
    add_box(parent, (0, 0, -(height / 2 - t / 2)), (width - 2 * t, depth, t), color)
    add_box(parent, (0, depth / 2 - t / 2, 0), (width - 2 * t, t, height - 2 * t), color)

def create_handle(parent, width, height, front_y, vertical=True):
    if vertical:
        length = min(0.24, max(0.12, height * 0.35))
        add_box(parent, (width / 2 - GAP - 0.05, front_y - 0.014, 0), (0.018, 0.018, length), HANDLE_COLOR)
    else:
        length = min(0.26, max(0.12, width * 0.5))
        add_box(parent, (0, front_y - 0.014, height / 2 - GAP - 0.045), (length, 0.018, 0.018), HANDLE_COLOR)

def create_cabinet(parent, width, depth, height, door_color, body_color, vertical=True):
    create_carcass(parent, width, depth, height, body_color)
    front_y = -depth / 2 - 0.004 - DOOR_T / 2
    add_box(parent, (0, front_y, 0), (width - 2 * GAP, DOOR_T, height - 2 * GAP), door_color)
    create_handle(parent, width, height, front_y - DOOR_T / 2, vertical)

def create_drawer(parent, width, depth, height, door_color, body_color):
    create_cabinet(parent, width, depth, height, door_color, body_color, vertical=False)

def create_open_shelf(parent, width, depth, height, door_color, body_color):
    create_carcass(parent, width, depth, height, body_color)
    if height > 0.55:
        add_box(parent, (0, 0.01, 0), (width - 2 * PANEL_T, depth - 0.04, 0.016), body_color)

def create_glass_cabinet(parent, width, depth, height, door_color, body_color):
    create_carcass(parent, width, depth, height, body_color)
    front_y = -depth / 2 - 0.004 - DOOR_T / 2
    frame = 0.055
    door_width = width - 2 * GAP
    door_height = height - 2 * GAP
    add_box(parent, (0, front_y, door_height / 2 - frame / 2), (door_width, DOOR_T, frame), door_color)
    add_box(parent, (0, front_y, -(door_height / 2 - frame / 2)), (door_width, DOOR_T, frame), door_color)
    add_box(parent, (-(door_width / 2 - frame / 2), front_y, 0), (frame, DOOR_T, door_height - 2 * frame), door_color)
    add_box(parent, (door_width / 2 - frame / 2, front_y, 0), (frame, DOOR_T, door_height - 2 * frame), door_color)
    add_box(parent, (0, front_y, 0), (door_width - 2 * frame + 0.01, 0.006, door_height - 2 * frame + 0.01), GLASS_COLOR, 0.45)
    create_handle(parent, width, height, front_y - DOOR_T / 2, vertical=True)

def create_appliance(parent, width, depth, height, face_color, body_color):
    add_box(parent, (0, 0.01, 0), (width - 0.006, depth - 0.03, height - 0.006), body_color)
    front_y = -depth / 2 - 0.012
    add_box(parent, (0, front_y, 0), (width - 0.006, 0.020, height - 0.006), face_color)
    create_handle(parent, width, height, front_y - 0.010, vertical=False)

def create_fridge(parent, width, depth, height, door_color, body_color):
    create_carcass(parent, width, depth, height, body_color)
    front_y = -depth / 2 - 0.004 - DOOR_T / 2
    center_gap = 0.006
    panel_width = (width - 2 * GAP - center_gap) / 2
    for side in (-1, 1):
        x = side * (center_gap / 2 + panel_width / 2 + GAP / 2)
        add_box(parent, (x, front_y, 0), (panel_width, DOOR_T, height - 2 * GAP), door_color)
        add_box(
            parent,
            (side * (center_gap / 2 + 0.05), front_y - DOOR_T / 2 - 0.014, 0),
            (0.018, 0.018, min(0.5, height * 0.6)),
            HANDLE_COLOR,
        )

BUILDERS = {
    "cabinet": create_cabinet,
    "drawer": create_drawer,
    "open_shelf": create_open_shelf,
    "glass": create_glass_cabinet,
    "fridge_double": create_fridge,
}

class KitchenMapView:
    def __init__(self, base, on_select):
        self.base = base
        self.on_select = on_select
        self.root = base.render.attachNewNode("kitchen-map")
        self.parts_by_id = {part.part_id: part for part in PARTS}
        self.parts_by_location = {}
        self.by_code = {}
        self.nodes = {}
        self.selected = None
        self.active = True
        self.pivot = base.render.attachNewNode("map-pivot")
        base.camera.reparentTo(self.pivot)
        self.cam_h = HOME_HEADING
        self.cam_p = HOME_PITCH
        self.cam_dist = 12.0
        self.perspective_lens = base.camNode.getLens()
        self.ortho_lens = OrthographicLens()
        self.ortho_lens.setNearFar(-100, 100)
        self.ortho = False
        self.rotating = False
        self.panning = False
        self.last_mouse = None
        self.drag_distance = 0.0
        self.build_room()
        self.build_parts()
        self.build_locations()
        self.build_group_labels()
        self.setup_picking()
        self.setup_input()
        self.reset_view()

    @property
    def valid_codes(self):
        return set(self.by_code)

    def show(self):
        self.active = True
        self.root.show()

    def hide(self):
        self.active = False
        self.root.hide()

    def build_room(self):
        static = self.root.attachNewNode("static")
        add_quad(static, [(-0.4, -0.5, 0), (5.0, -0.5, 0), (5.0, 4.8, 0), (-0.4, 4.8, 0)], FLOOR_COLOR, "floor")
        add_quad(
            static, [(-0.01, -0.4, 0), (-0.01, 4.8, 0), (-0.01, 4.8, 2.7), (-0.01, -0.4, 2.7)], WALL_COLOR, "left-wall"
        )
        add_quad(static, [(-0.4, 4.41, 0), (5.0, 4.41, 0), (5.0, 4.41, 2.7), (-0.4, 4.41, 2.7)], WALL_COLOR, "top-wall")
        for x0, x1, y0, y1, z0, z1, color in STATIC_BOXES:
            add_box(static, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), color)
        static.flattenStrong()

    def build_parts(self):
        parent = self.root.attachNewNode("cabinet-parts")
        for part in PARTS:
            node = parent.attachNewNode("part-" + part.part_id)
            node.setPos(*part.center)
            node.setH(HEADINGS[part.front_direction])
            width, depth, height = local_size(part)
            geometry = node.attachNewNode("geometry")
            if part.part_type == "countertop":
                add_box(geometry, (0, 0, 0), (width, depth, height), CT_COLOR)
            elif part.part_type == "appliance":
                face = APPLIANCE_COLORS.get(part.part_id, (0.5, 0.5, 0.52))
                create_appliance(geometry, width, depth, height, face, tuple(channel * 0.75 for channel in face))
            else:
                door_color = GROUP_COLORS[part.group]
                body_color = tuple(channel * 0.72 for channel in door_color)
                BUILDERS[part.part_type](geometry, width, depth, height, door_color, body_color)
            geometry.flattenStrong()
            self.nodes[part.part_id] = node
            if part.aux or part.location_code is None:
                continue
            self.parts_by_location.setdefault(part.location_code, []).append(part.part_id)
            collision = CollisionNode("pick-" + part.part_id)
            collision.addSolid(CollisionBox(Point3(0, 0, 0), width / 2, depth / 2, height / 2))
            collision.setIntoCollideMask(PICK_MASK)
            collision.setFromCollideMask(BitMask32.allOff())
            collision_node = node.attachNewNode(collision)
            collision_node.setTag("code", part.location_code)

    def build_locations(self):
        for code, part_ids in self.parts_by_location.items():
            parts = [self.parts_by_id[part_id] for part_id in part_ids]
            # box around all the parts of this location
            low = [min(part.center[i] - part.size[i] / 2 for part in parts) for i in range(3)]
            high = [max(part.center[i] + part.size[i] / 2 for part in parts) for i in range(3)]
            center = tuple((low[i] + high[i]) / 2 for i in range(3))
            size = tuple(high[i] - low[i] for i in range(3))
            name, location_type = LOCATION_INFO[code]
            location = Location(code, parts[0].group, center, size, parts[0].front_direction, location_type, name)
            self.by_code[code] = location
            if location_type == "countertop":
                label_position = (center[0], center[1], high[2] + 0.10)
                label_scale = 0.06
            else:
                cx, cy, cz = location.center
                sx, sy, _ = location.size
                label_position = {
                    "+x": (cx + sx / 2 + 0.055, cy, cz),
                    "-x": (cx - sx / 2 - 0.055, cy, cz),
                    "+y": (cx, cy + sy / 2 + 0.055, cz),
                    "-y": (cx, cy - sy / 2 - 0.055, cz),
                }[location.front_direction]
                label_scale = 0.055
            create_label(self.root, code, label_position, label_scale)

    def build_group_labels(self):
        parent = self.root.attachNewNode("group-labels")
        for letter, position in GROUP_LABELS.items():
            color = GROUP_COLORS[letter]
            label_color = (min(1, color[0] * 1.15), min(1, color[1] * 1.15), min(1, color[2] * 1.15), 1)
            create_label(parent, letter, position, 0.26, label_color)

    def setup_picking(self):
        self.picker = CollisionTraverser()
        self.queue = CollisionHandlerQueue()
        collision = CollisionNode("mouse-ray")
        self.ray = CollisionRay()
        collision.addSolid(self.ray)
        collision.setFromCollideMask(PICK_MASK)
        collision.setIntoCollideMask(BitMask32.allOff())
        ray_node = self.base.cam.attachNewNode(collision)
        self.picker.addCollider(ray_node, self.queue)

    def setup_input(self):
        self.base.accept("mouse1", self.left_down)
        self.base.accept("mouse1-up", self.left_up)
        self.base.accept("mouse3", self.right_down)
        self.base.accept("mouse3-up", self.right_up)
        self.base.accept("wheel_up", self.zoom, [0.88])
        self.base.accept("wheel_down", self.zoom, [1.14])
        self.base.accept("t", self.top_view)
        self.base.accept("r", self.reset_view)
        self.base.taskMgr.add(self.mouse_task, "map-mouse-task")

    def mouse_in_map(self):
        if not self.base.mouseWatcherNode.hasMouse():
            return False
        mouse = self.base.mouseWatcherNode.getMouse()
        return mouse.x < 0.55 and -0.78 < mouse.y < 0.82

    def left_down(self):
        if self.active and self.mouse_in_map():
            self.rotating = True
            self.drag_distance = 0.0

    def left_up(self):
        if not self.active:
            return
        self.rotating = False
        if self.drag_distance < 0.02 and self.mouse_in_map():
            self.pick()

    def right_down(self):
        if self.active and self.mouse_in_map():
            self.panning = True

    def right_up(self):
        self.panning = False

    def zoom(self, factor):
        if not self.active or not self.mouse_in_map():
            return
        if self.ortho:
            width, height = self.ortho_lens.getFilmSize()
            if 2.0 <= height * factor <= 20.0:
                self.ortho_lens.setFilmSize(width * factor, height * factor)
        else:
            self.cam_dist = max(2.0, min(30.0, self.cam_dist * factor))
        self.apply_camera()

    def mouse_task(self, task):
        if not self.active or not self.base.mouseWatcherNode.hasMouse():
            self.last_mouse = None
            return task.cont
        mouse = self.base.mouseWatcherNode.getMouse()
        x, y = mouse.x, mouse.y
        if self.last_mouse is not None:
            dx = x - self.last_mouse[0]
            dy = y - self.last_mouse[1]
            if self.rotating and (dx or dy):
                self.set_ortho(False)  # rotating leaves top view
                self.drag_distance += abs(dx) + abs(dy)
                self.cam_h -= dx * 160
                self.cam_p = max(-90, min(10, self.cam_p - dy * 120))
                self.apply_camera()
            elif self.panning and (dx or dy):
                camera_rotation = self.base.camera.getQuat(self.base.render)
                move = (camera_rotation.getRight() * dx + camera_rotation.getUp() * dy) * self.cam_dist * 0.5
                self.pivot.setPos(self.pivot.getPos() - move)
        self.last_mouse = (x, y)
        return task.cont

    def set_ortho(self, enabled):
        if enabled == self.ortho:
            return
        if enabled:
            across, updown = self.screen_span()
            aspect = max(0.2, self.base.getAspectRatio())
            height = max(updown / USABLE_HEIGHT, across / USABLE_WIDTH / aspect) * MARGIN
            self.ortho_lens.setFilmSize(height * aspect, height)
            self.base.camNode.setLens(self.ortho_lens)
        else:
            self.base.camNode.setLens(self.perspective_lens)
        self.ortho = enabled

    def screen_span(self):
        heading = math.radians(self.cam_h)
        pitch = math.radians(abs(self.cam_p))
        span_x, span_y, span_z = ROOM_SPAN
        across = span_x * abs(math.cos(heading)) + span_y * abs(math.sin(heading))
        depth = span_x * abs(math.sin(heading)) + span_y * abs(math.cos(heading))
        updown = depth * math.sin(pitch) + span_z * math.cos(pitch)
        return across, updown

    def frame_distance(self):
        # how far back the camera has to be so the whole room fits next to the side panel
        across, updown = self.screen_span()
        h_fov, v_fov = self.perspective_lens.getFov()
        by_width = (across / USABLE_WIDTH / 2) / math.tan(math.radians(h_fov / 2))
        by_height = (updown / USABLE_HEIGHT / 2) / math.tan(math.radians(v_fov / 2))
        return max(by_width, by_height) * MARGIN

    def visible_half_width(self):
        if self.ortho:
            return self.ortho_lens.getFilmSize()[0] / 2
        h_fov = self.base.camLens.getFov()[0]
        return self.cam_dist * math.tan(math.radians(h_fov / 2))

    def visible_half_height(self):
        if self.ortho:
            return self.ortho_lens.getFilmSize()[1] / 2
        v_fov = self.base.camLens.getFov()[1]
        return self.cam_dist * math.tan(math.radians(v_fov / 2))

    def apply_camera(self):
        self.pivot.setHpr(self.cam_h, self.cam_p, 0)
        # move the camera sideways so the room isnt hidden behind the side panel
        self.base.camera.setPos(PANEL_NDC * self.visible_half_width(), -self.cam_dist, -VERT_NDC * self.visible_half_height())
        self.base.camera.setHpr(0, 0, 0)

    def set_view(self, heading, pitch, pivot, zoom=1.0):
        self.set_ortho(False)
        self.cam_h, self.cam_p = heading, pitch
        self.cam_dist = self.frame_distance() * zoom
        self.pivot.setPos(*pivot)
        self.apply_camera()

    def reset_view(self):
        if self.active:
            self.set_view(HOME_HEADING, HOME_PITCH, ROOM_CENTER)

    def top_view(self):
        if not self.active:
            return
        self.set_view(0, -90, (ROOM_CENTER[0], ROOM_CENTER[1], 0.0))
        self.cam_dist = 20.0
        self.set_ortho(True)
        self.apply_camera()

    def focus(self, code):
        location = self.by_code.get(code)
        if location is None:
            return
        # aim halfway between the compartment and the room centre so the rest of the kitchen stays in view
        pivot = [(a + b) / 2 for a, b in zip(location.center, ROOM_CENTER)]
        self.set_view(FOCUS_HEADINGS.get(location.front_direction, HOME_HEADING), -28, pivot, 0.92)

    def pick(self):
        mouse = self.base.mouseWatcherNode.getMouse()
        # fire one ray from the camera through the click point
        self.ray.setFromLens(self.base.camNode, mouse.x, mouse.y)
        self.picker.traverse(self.root)
        if self.queue.getNumEntries() == 0:
            self.select(None)              # clicked empty space: deselect
            return
        self.queue.sortEntries()           # nearest hit first
        # every collision box was tagged with its location code at build time
        code = self.queue.getEntry(0).getIntoNodePath().getNetTag("code")
        self.select(code or None)

    def select(self, code, focus=False):
        if code:
            code = code.upper()
        if self.selected:
            for part_id in self.parts_by_location.get(self.selected, []):
                self.nodes[part_id].clearColorScale()
        self.selected = code
        if code and code in self.by_code:
            for part_id in self.parts_by_location[code]:
                self.nodes[part_id].setColorScale(1.55, 1.55, 1.55, 1)
            if focus:
                self.focus(code)
            self.on_select(code)
        else:
            self.on_select(None)
