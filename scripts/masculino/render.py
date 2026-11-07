"""Importa el GLB y renderiza vistas con grupos resaltados.
Uso: Blender --background --factory-startup --python render.py -- <glb> <dir_png>
"""
import bpy, sys, math
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
GLB, OUTD = args[0], args[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene

meshes = [o for o in sc.objects if o.type == "MESH"]
print("mallas importadas:", sorted(o.name for o in meshes))
print("tris:", sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes))
zs = [(o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box]
xs = [(o.matrix_world @ Vector(c)).x for o in meshes for c in o.bound_box]
ys = [(o.matrix_world @ Vector(c)).y for o in meshes for c in o.bound_box]
print("bbox z", min(zs), max(zs), "x", min(xs), max(xs), "y", min(ys), max(ys))

def mat(name, rgb, rough=0.55, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m

def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)

M_MUSC = mat("neutro", srgb("#3c4049"))
M_BASE = mat("base", srgb("#262930"))
M_HUESO = mat("hueso", srgb("#55534e"))
M_AMAR = mat("amarillo", srgb("#FBE049"), rough=0.45, emit=0.15)

def grupo(o):
    n = o.name
    for suf in ("_izq", "_der"):
        if n.endswith(suf):
            return n[: -len(suf)]
    return n

# mundo y luz
w = bpy.data.worlds.new("w"); sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (*srgb("#0b0c0f"), 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0

def luz(nombre, loc, energia, tam=3):
    l = bpy.data.lights.new(nombre, "AREA"); l.energy = energia; l.size = tam
    o = bpy.data.objects.new(nombre, l); sc.collection.objects.link(o)
    o.location = loc
    d = Vector((0, 0, 0.1)) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o

cam_d = bpy.data.cameras.new("cam"); cam_d.type = "ORTHO"; cam_d.ortho_scale = 2.05
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam

sc.render.resolution_x, sc.render.resolution_y = 900, 1600
sc.render.film_transparent = False
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        sc.render.engine = eng; break
    except TypeError:
        pass
print("motor:", sc.render.engine)
sc.view_settings.view_transform = "Standard"

VISTAS = [
    ("frente_pecho-core-cuadriceps", -1, {"pecho", "core", "cuadriceps"}),
    ("espalda_espalda-gluteos-femorales", 1, {"espalda", "gluteos", "femorales"}),
    ("frente_hombros-biceps-antebrazos-aductores", -1, {"hombros", "biceps", "antebrazos", "aductores"}),
    ("espalda_triceps-lumbares-pantorrillas-abductores", 1, {"triceps", "lumbares", "pantorrillas", "abductores"}),
]
luces = []
for nombre, lado, resalta in VISTAS:
    for l in luces:
        bpy.data.objects.remove(l)
    luces = [luz("key", (lado * -2.5 + 2.0, lado * 4.0, 2.5), 900),
             luz("fill", (-3.0, lado * 3.0, 0.5), 300),
             luz("rim", (0.5, -lado * 4.0, 3.0), 700)]
    for o in meshes:
        g = grupo(o)
        m = M_AMAR if g in resalta else (M_BASE if g == "base_musculos" else (M_HUESO if g == "base_huesos" else M_MUSC))
        o.data.materials.clear(); o.data.materials.append(m)
    cam.location = (0, lado * 6.0, 0.0)
    cam.rotation_euler = (math.pi / 2, 0, 0 if lado < 0 else math.pi)
    sc.render.filepath = f"{OUTD}/{nombre}.png"
    bpy.ops.render.render(write_still=True)
    print("render", sc.render.filepath)
