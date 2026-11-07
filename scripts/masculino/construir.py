"""Construye el GLB de grupos musculares a partir de Startup.blend (Z-Anatomy).

Uso: Blender --background --factory-startup --disable-autoexec Startup.blend \
       --python construir.py -- <dir_salida> [presupuesto_tris]
"""
import bpy, bmesh, json, re, sys, math
import numpy as np
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]
TOTAL = int(args[1]) if len(args) > 1 else 48000
PRES_HUESOS = 5000
PRES_BASE = 10000
MIN_BUCKET = 400

# ---------------- mapeo ----------------
EXCLUIR_SIEMPRE = [
    r"bursa", r"sheath", r"fascia", r"retinacul", r"septum", r"aponeuros",
    r"ligament", r"tendinous", r"\btarsus\b", r"trochlea", r"\.g$", r"\.j$",
]
GRUPOS = [
    ("pecho", [r"pectoralis major", r"pectoralis minor"]),
    ("hombros", [r"deltoid muscle", r"supraspinatus", r"infraspinatus", r"subscapularis"]),
    ("espalda", [r"latissimus dorsi", r"trapezius", r"rhomboid", r"teres major", r"teres minor",
                 r"levator scapulae", r"serratus posterior"]),
    ("biceps", [r"biceps brachii", r"^brachialis muscle", r"coracobrachialis"]),
    ("triceps", [r"triceps brachii", r"anconeus"]),
    ("antebrazos", [r"brachioradialis", r"flexor carpi", r"extensor carpi", r"palmaris longus",
                    r"pronator", r"^supinator", r"flexor digitorum superficialis",
                    r"flexor digitorum profundus", r"flexor pollicis longus", r"^extensor digitorum$",
                    r"extensor digiti minimi", r"extensor indicis", r"extensor pollicis",
                    r"abductor pollicis longus"]),
    ("core", [r"rectus abdominis", r"abdominal oblique", r"transversus abdominis", r"pyramidalis",
              r"linea alba"]),
    ("lumbares", [r"iliocostalis (lumborum|thoracis)", r"longissimus thoracis", r"spinalis thoracis",
                  r"multifidus (lumborum|thoracis)", r"quadratus lumborum",
                  r"interspinales (lumborum|thoracis)", r"intertransversarii lumborum",
                  r"semispinalis thoracis", r"^rotatores"]),
    ("cuadriceps", [r"rectus femoris", r"vastus"]),
    ("femorales", [r"biceps femoris", r"semitendinosus", r"semimembranosus"]),
    ("gluteos", [r"gluteus maximus", r"piriformis", r"gemellus", r"obturator internus",
                 r"quadratus femoris"]),
    ("abductores", [r"gluteus medius", r"gluteus minimus", r"tensor fasciae latae"]),
    ("pantorrillas", [r"gastrocnemius", r"soleus", r"plantaris muscle", r"calcaneal tendon"]),
    ("aductores", [r"adductor (longus|brevis|magnus|minimus)", r"gracilis", r"pectineus",
                   r"obturator externus"]),
]
# musculos sin grupo de entreno pero visibles: dan silueta (cabeza, cuello, manos, pies, tibial...)
BASE_MUSC = [
    r"frontalis", r"occipitalis", r"temporoparietalis", r"temporalis", r"masseter",
    r"zygomaticus", r"orbicularis", r"nasalis", r"procerus", r"risorius", r"depressor",
    r"levator labii", r"levator anguli", r"levator nasolabialis", r"mentalis", r"bucinator",
    r"corrugator", r"sternocleidomastoid", r"scalenus", r"splenius", r"semispinalis (colli|capitis)",
    r"longissimus (capitis|colli)", r"iliocostalis colli", r"spinalis (capitis|colli)",
    r"multifidus colli", r"omohyoid", r"sternohyoid", r"sternothyroid", r"thyrohyoid",
    r"digastric", r"mylohyoid", r"stylohyoid", r"geniohyoid",
    # mano
    r"of hand", r"abductor pollicis brevis", r"flexor pollicis brevis", r"adductor pollicis",
    r"opponens pollicis", r"palmar interossei",
    # pie
    r"of foot", r"abductor hallucis", r"adductor hallucis", r"flexor hallucis brevis",
    r"extensor hallucis brevis", r"extensor digitorum brevis", r"flexor digitorum brevis",
    r"quadratus plantae", r"plantar interossei",
    # pierna / muslo / torso
    r"tibialis anterior", r"tibialis posterior", r"extensor digitorum longus",
    r"extensor hallucis longus", r"fibularis", r"flexor digitorum longus", r"flexor hallucis longus",
    r"popliteus", r"sartorius", r"iliotibial tract", r"serratus anterior",
    r"external intercostal",
]
BASE_HUESOS = [
    r"phalanx", r"metacarpal", r"metatarsal", r"^(capitate|hamate|lunate|pisiform|scaphoid|trapezium|trapezoid|triquetrum)",
    r"^(calcaneus|talus|navicular|cuboid)", r"cuneiform", r"^patella", r"^clavicle",
    r"^(frontal|parietal|occipital|temporal|sphenoid|zygomatic|nasal) bone", r"^maxilla",
    r"^mandible", r"^sternum", r"manubrium", r"body of sternum", r"xiphoid",
]


def base_name(n):
    return re.sub(r"\.(l|r)(\.\d+)?$", "", n)


def side_from_name(n):
    m = re.search(r"\.(l|r)(\.\d+)?$", n)
    return {"l": "izq", "r": "der"}[m.group(1)] if m else None


def clasifica_musculo(n):
    b = base_name(n).strip("()[] ").lower()
    for rx in EXCLUIR_SIEMPRE:
        if re.search(rx, n.lower()):
            return "excluido", "tejido no muscular / auxiliar"
    for g, rxs in GRUPOS:
        for rx in rxs:
            if re.search(rx, b):
                return g, rx
    for rx in BASE_MUSC:
        if re.search(rx, b):
            return "base_musculos", rx
    return "excluido", "musculo profundo/interno sin grupo"


def clasifica_hueso(n):
    b = base_name(n).strip("()[] ").lower()
    for rx in BASE_HUESOS:
        if re.search(rx, b):
            return "base_huesos", rx
    return None, None


def objs_of(colname):
    col = bpy.data.collections[colname]
    s = set(col.objects)
    for c in col.children_recursive:
        s |= set(c.objects)
    return [o for o in s if o.type == "MESH" and o.data and len(o.data.polygons) > 0]


def world_arrays(o):
    me = o.data
    nv = len(me.vertices)
    co = np.empty(nv * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    M = np.array(o.matrix_world)
    co = co @ M[:3, :3].T + M[:3, 3]
    nl = len(me.loops)
    lv = np.empty(nl, dtype=np.int64)
    me.loops.foreach_get("vertex_index", lv)
    np_ = len(me.polygons)
    ls = np.empty(np_, dtype=np.int64)
    lt = np.empty(np_, dtype=np.int64)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    return co, lv, ls, lt


def build_mesh(name, parts):
    cos, lvs, lss, lts = [], [], [], []
    voff = loff = 0
    for co, lv, ls, lt in parts:
        cos.append(co); lvs.append(lv + voff); lss.append(ls + loff); lts.append(lt)
        voff += len(co); loff += len(lv)
    co = np.concatenate(cos); lv = np.concatenate(lvs); ls = np.concatenate(lss)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(co))
    me.vertices.foreach_set("co", co.astype(np.float32).ravel())
    me.loops.add(len(lv))
    me.loops.foreach_set("vertex_index", lv.astype(np.int32))
    me.polygons.add(len(ls))
    me.polygons.foreach_set("loop_start", ls.astype(np.int32))
    me.update(calc_edges=True)
    me.validate(clean_customdata=True)
    return me


def tris(me):
    lt = np.empty(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get("loop_total", lt)
    return int((lt - 2).sum())


def area(me):
    a = np.empty(len(me.polygons), dtype=np.float64)
    me.polygons.foreach_get("area", a)
    return float(a.sum())


# ---------------- recoger ----------------
mapeo = {}
buckets = {}  # (grupo, lado) -> [arrays]
centros = {}

def add(o, grupo, motivo, coleccion):
    co, lv, ls, lt = world_arrays(o)
    lado = side_from_name(o.name)
    cx = float(co[:, 0].mean())
    if lado is None:
        lado = "centro"
    mapeo[o.name] = {"grupo": grupo, "lado": lado, "regla": motivo, "coleccion": coleccion,
                     "tris_orig": int((lt - 2).sum()), "cx": round(cx, 4)}
    if grupo == "excluido":
        return
    key = (grupo, lado)
    buckets.setdefault(key, []).append((co, lv, ls, lt))
    c = centros.setdefault(grupo, {}).setdefault(lado, [])
    c.append(co.mean(axis=0))

for o in objs_of("4: Muscular system"):
    g, m = clasifica_musculo(o.name)
    add(o, g, m, "4: Muscular system")
for o in objs_of("1: Skeletal system"):
    g, m = clasifica_hueso(o.name)
    if g:
        add(o, g, m, "1: Skeletal system")

# lados sin sufijo: por posicion X (se decide el signo con los que si lo tienen)
lx = [v["cx"] for v in mapeo.values() if v["lado"] == "izq"]
rx = [v["cx"] for v in mapeo.values() if v["lado"] == "der"]
signo_izq = 1 if np.median(lx) > 0 else -1
print("signo X de .l:", signo_izq, "mediana l", np.median(lx), "mediana r", np.median(rx))

# rehacer los 'centro' de piezas claramente laterales
for name, v in mapeo.items():
    if v["lado"] == "centro" and v["grupo"] != "excluido" and abs(v["cx"]) > 0.02:
        v["lado"] = "izq" if (v["cx"] > 0) == (signo_izq > 0) else "der"
        v["lado_por_posicion"] = True
# reconstruir buckets con el lado definitivo
buckets = {}
for o in objs_of("4: Muscular system") + objs_of("1: Skeletal system"):
    v = mapeo.get(o.name)
    if not v or v["grupo"] == "excluido":
        continue
    buckets.setdefault((v["grupo"], v["lado"]), []).append(world_arrays(o))

# ---------------- mallas ----------------
sc = bpy.context.scene
objs = {}
for (g, lado), parts in sorted(buckets.items()):
    nm = g if lado == "centro" else f"{g}_{lado}"
    me = build_mesh(nm, parts)
    ob = bpy.data.objects.new(nm, me)
    sc.collection.objects.link(ob)
    ob["grupo"] = g
    ob["lado"] = lado
    objs[nm] = ob

# bbox global, orientacion (frente = -Y en Blender), escala y centrado
allc = np.concatenate([np.array([v.co for v in ob.data.vertices]) for ob in objs.values()])
mn, mx = allc.min(0), allc.max(0)
alto = mx[2] - mn[2]
print("bbox original", mn, mx, "alto", alto)

def cy(prefix):
    pts = [np.array([v.co for v in ob.data.vertices]).mean(0) for n, ob in objs.items() if n.startswith(prefix)]
    return float(np.mean([p[1] for p in pts]))
y_pecho, y_glut = cy("pecho"), cy("gluteos")
print("y pecho", y_pecho, "y gluteos", y_glut)
rot = Matrix.Identity(4)
if y_pecho > y_glut:  # el pecho mira a +Y: girar 180 para que mire a -Y (=> +Z en glTF)
    rot = Matrix.Rotation(math.pi, 4, "Z")
    print("girado 180 en Z")
# tras el giro, sin la conversion del exportador, "izq" (lado izquierdo del sujeto)
s = 1.8 / alto
centro = Vector(((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2))
T = Matrix.Scale(s, 4) @ rot @ Matrix.Translation(-centro)
for ob in objs.values():
    ob.data.transform(T)

# soldar, decimar
area_g = {n: area(ob.data) for n, ob in objs.items()}
area_musc = sum(a for n, a in area_g.items() if not n.startswith("base_"))
area_base = sum(a for n, a in area_g.items() if n.startswith("base_musculos"))
area_hue = sum(a for n, a in area_g.items() if n.startswith("base_huesos"))
pres_musc = TOTAL - PRES_BASE - PRES_HUESOS
resumen = {}
dg = bpy.context.evaluated_depsgraph_get()
for n, ob in objs.items():
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(ob.data); bm.free()
    t0 = tris(ob.data)
    if n.startswith("base_musculos"):
        obj_t = PRES_BASE * area_g[n] / area_base
    elif n.startswith("base_huesos"):
        obj_t = PRES_HUESOS * area_g[n] / area_hue
    else:
        obj_t = max(MIN_BUCKET, pres_musc * area_g[n] / area_musc)
    ratio = min(1.0, obj_t / max(t0, 1))
    mod = ob.modifiers.new("dec", "DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    dg.update()
    ev = ob.evaluated_get(dg)
    nme = bpy.data.meshes.new_from_object(ev)
    old = ob.data
    ob.modifiers.clear()
    ob.data = nme
    bpy.data.meshes.remove(old)
    nme.name = n
    nme.shade_smooth()
    resumen[n] = {"tris_antes": t0, "objetivo": int(obj_t), "tris_despues": tris(nme)}

# materiales: uno por grupo (izq y der comparten)
COLOR = {"base_musculos": (0.32, 0.33, 0.36, 1), "base_huesos": (0.62, 0.60, 0.56, 1)}
mats = {}
for n, ob in objs.items():
    g = ob["grupo"]
    if g not in mats:
        m = bpy.data.materials.new(g)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        col = COLOR.get(g, (0.55, 0.30, 0.30, 1))
        bsdf.inputs["Base Color"].default_value = col
        bsdf.inputs["Roughness"].default_value = 0.6
        m.diffuse_color = col
        mats[g] = m
    ob.data.materials.clear()
    ob.data.materials.append(mats[g])

# exportar solo lo nuestro
for o in sc.objects:
    o.select_set(False)
for ob in objs.values():
    ob.hide_set(False); ob.hide_viewport = False; ob.hide_render = False
    ob.select_set(True)
bpy.context.view_layer.objects.active = next(iter(objs.values()))
glb = OUT + "/squeez-musculos-zanatomy.glb"
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_extras=True,
                          export_materials="EXPORT", export_animations=False,
                          export_cameras=False, export_lights=False)

total = sum(v["tris_despues"] for v in resumen.values())
with open(OUT + "/mapeo-musculos.json", "w") as f:
    json.dump({"grupos": [g for g, _ in GRUPOS],
               "nota_lados": "izq/der = lado del sujeto (anatomico), segun sufijo .l/.r de Z-Anatomy",
               "objetos": dict(sorted(mapeo.items()))}, f, indent=1, ensure_ascii=False)
with open(OUT + "/_resumen_build.json", "w") as f:
    json.dump({"total_tris": total, "alto_original": float(alto), "escala": float(s),
               "mallas": resumen}, f, indent=1)
print("TOTAL TRIS", total)
