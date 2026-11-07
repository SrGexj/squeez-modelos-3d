"""Renderiza frente y espalda de un GLB con grupos resaltados en amarillo de marca.
Pies alineados a la misma linea en todas las variantes (comparables lado a lado).
Uso: Blender --background --factory-startup --disable-autoexec --python render.py -- <glb> <dir_png> <prefijo>
"""
import bpy, sys, math
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
GLB, OUTD, PRE = args[0], args[1], args[2]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene
meshes = [o for o in sc.objects if o.type == "MESH"]
print("tris:", sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes))
zs = [(o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box]
zmin = min(zs)
print("alto:", max(zs) - zmin)


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def mat(name, hexc, rough=0.55, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    rgb = srgb(hexc)
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


M_MUSC = mat("neutro", "#3c4049")
M_BASE = mat("base", "#262930")
M_PIEL = mat("piel", "#30333a", rough=0.6)
M_HUESO = mat("hueso", "#55534e")
M_AMAR = mat("amarillo", "#FBE049", rough=0.45, emit=0.15)


def grupo(o):
    return o.get("grupo") or o.name.rsplit("_", 1)[0]


w = bpy.data.worlds.new("w"); sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (*srgb("#0b0c0f"), 1)


def luz(nombre, loc, energia, tam=3):
    l = bpy.data.lights.new(nombre, "AREA"); l.energy = energia; l.size = tam
    o = bpy.data.objects.new(nombre, l); sc.collection.objects.link(o)
    o.location = loc
    l.use_shadow = nombre != "fill"
    d = Vector((0, 0, 0.1)) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o


cam_d = bpy.data.cameras.new("cam"); cam_d.type = "ORTHO"; cam_d.ortho_scale = 2.05
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 900, 1600
sc.render.engine = "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"

VISTAS = [
    ("frente_pecho-hombros-cuadriceps", -1, {"pecho", "hombros", "cuadriceps"}),
    ("espalda_espalda-gluteos-femorales", 1, {"espalda", "gluteos", "femorales"}),
]
import os
PALETA = {"pecho": "#e6194b", "hombros": "#f58231", "espalda": "#ffe119", "biceps": "#3cb44b",
          "triceps": "#42d4f4", "antebrazos": "#4363d8", "core": "#911eb4", "lumbares": "#f032e6",
          "cuadriceps": "#bfef45", "femorales": "#fabed4", "gluteos": "#469990", "abductores": "#dcbeff",
          "pantorrillas": "#9A6324", "aductores": "#fffac8"}
MAPA = {g: mat("m_" + g, c) for g, c in PALETA.items()}
if os.environ.get("MAPA"):
    VISTAS = [("mapa_frente", -1, set()), ("mapa_espalda", 1, set())]
if os.environ.get("PERFIL"):
    VISTAS = [("perfil", 0, {"pecho", "gluteos"})]
luces = []
for nombre, lado, resalta in VISTAS:
    for l in luces:
        bpy.data.objects.remove(l)
    luces = [luz("key", (lado * -2.5 + 2.0, lado * 4.0, 2.5), 900),
             luz("fill", (-3.0, lado * 3.0, 0.5), 300),
             luz("rim", (0.5, -lado * 4.0, 3.0), 700)]
    for o in meshes:
        g = grupo(o)
        if g in resalta:
            m = M_AMAR
        elif os.environ.get("MAPA") and g in MAPA:
            m = MAPA[g]
        elif g == "base_musculos":
            m = M_BASE
        elif g == "base_huesos":
            m = M_HUESO
        elif g == "base_piel":
            m = M_PIEL
        else:
            m = M_MUSC
        o.data.materials.clear(); o.data.materials.append(m)
    cam.location = (0, lado * 6.0, zmin + 0.9)
    cam.rotation_euler = (math.pi / 2, 0, 0 if lado < 0 else math.pi)
    if lado == 0:
        for l in luces:
            l.location = (4.0, l.location.y * 0.5 - 1, l.location.z)
            l.rotation_euler = (Vector((0, 0, 0.1)) - l.location).to_track_quat("-Z", "Y").to_euler()
        cam.location = (6.0, 0, zmin + 0.9)
        cam.rotation_euler = (math.pi / 2, 0, math.pi / 2)
    sc.render.filepath = f"{OUTD}/{PRE}_{nombre}.png"
    bpy.ops.render.render(write_still=True)
    print("render", sc.render.filepath)
