"""Variante A: reproporciona el modelo masculino de Z-Anatomy a proporciones femeninas.

Deformacion por campo continuo (la misma funcion para todas las mallas, asi musculos
vecinos siguen encajando). No cambia nombres de nodos, extras ni materiales.

Uso: Blender --background --factory-startup --disable-autoexec --python variante_a.py -- \
       <masculino.glb> <salida.glb>
Coordenadas (Blender tras importar): Z arriba, frente = -Y, +X = izquierda del sujeto.
"""
import bpy, sys, math
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = args[0], args[1]
ALTURA = 1.65

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
objs = sorted([o for o in bpy.context.scene.objects if o.type == "MESH"], key=lambda o: o.name)


def grupo(o):
    return o.get("grupo", o.name.rsplit("_", 1)[0])


def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def interp(z, pts):
    zs, vs = zip(*pts)
    return np.interp(z, zs, vs)


# coordenadas de mundo de todo
data = {}
for o in objs:
    M = np.array(o.matrix_world)
    co = np.array([v.co[:] for v in o.data.vertices])
    co = co @ M[:3, :3].T + M[:3, 3]
    data[o.name] = co

# ---------- peso de brazo por vertice ----------
BRAZO = {"biceps", "triceps", "antebrazos"}


def peso_brazo_directo(o, co):
    g = grupo(o)
    if g in BRAZO:
        return np.ones(len(co))
    if g == "hombros":
        return ss(0.13, 0.21, np.abs(co[:, 0]))
    return np.zeros(len(co))


# mallas de musculo con grupo: peso directo; mallas base: media de los 8 vecinos
# etiquetados mas cercanos (asi la mano sigue al antebrazo y la fascia lata al muslo)
from mathutils import kdtree
etiq_co, etiq_w = [], []
for o in objs:
    if not grupo(o).startswith("base_"):
        etiq_co.append(data[o.name]); etiq_w.append(peso_brazo_directo(o, data[o.name]))
etiq_co = np.concatenate(etiq_co); etiq_w = np.concatenate(etiq_w)
kd = kdtree.KDTree(len(etiq_co))
for i, c in enumerate(etiq_co):
    kd.insert(c, i)
kd.balance()


def peso_brazo(o, co):
    if not grupo(o).startswith("base_"):
        return peso_brazo_directo(o, co)
    w = np.empty(len(co))
    for i, c in enumerate(co):
        r = kd.find_n(c, 8)
        w[i] = np.mean([etiq_w[j] for _, j, _ in r])
    w = ss(0.25, 0.75, w)
    # cabeza y cuello nunca son brazo
    w *= 1 - ss(0.6, 0.66, co[:, 2]) * (np.abs(co[:, 0]) < 0.12)
    return w


W = {o.name: peso_brazo(o, data[o.name]) for o in objs}

# ---------- peso de pierna ----------
PIERNA = {"cuadriceps", "femorales", "aductores", "pantorrillas"}


def peso_pierna(o, co, wa):
    z = co[:, 2]
    w = 1 - ss(-0.12, 0.02, z)
    return w * (1 - wa)


WL = {o.name: peso_pierna(o, data[o.name], W[o.name]) for o in objs}

# ---------- ejes de brazo y pierna (centro por franjas de z, por lado) ----------
def ejes(selector, z0, z1, paso=0.02):
    zb = np.arange(z0, z1 + paso, paso)
    res = {}
    for lado, sg in (("izq", 1), ("der", -1)):
        pts = []
        for o in objs:
            co = data[o.name]
            m = selector(o, co) & (np.sign(co[:, 0]) == sg)
            pts.append(co[m])
        P = np.concatenate(pts)
        cx, cy = [], []
        for zz in zb:
            mm = np.abs(P[:, 2] - zz) < paso
            if mm.sum() < 5:
                cx.append(np.nan); cy.append(np.nan); continue
            cx.append(np.median(P[mm, 0])); cy.append(np.median(P[mm, 1]))
        cx, cy = np.array(cx), np.array(cy)
        ok = ~np.isnan(cx)
        cx = np.interp(zb, zb[ok], cx[ok]); cy = np.interp(zb, zb[ok], cy[ok])
        k = np.ones(5) / 5
        cx = np.convolve(np.pad(cx, 2, mode="edge"), k, "valid")
        cy = np.convolve(np.pad(cy, 2, mode="edge"), k, "valid")
        res[lado] = (zb, cx, cy)
    return res


EJE_BRAZO = ejes(lambda o, co: W[o.name] > 0.9, -0.45, 0.62)
EJE_PIERNA = ejes(lambda o, co: (WL[o.name] > 0.9) & (grupo(o) != "base_huesos"), -0.9, 0.02)


def eje(E, lado_sg, z):
    zb, cx, cy = E["izq" if lado_sg > 0 else "der"]
    return np.interp(z, zb, cx), np.interp(z, zb, cy)


# ---------- perfiles ----------
# ancho lateral del tronco (sobre x=0) segun altura (coordenadas del masculino)
SX = [(-0.9, 0.98), (-0.55, 0.97), (-0.32, 1.03), (-0.15, 1.08), (-0.04, 1.13), (0.04, 1.12),
      (0.12, 1.0), (0.21, 0.85), (0.27, 0.87), (0.38, 0.91), (0.47, 0.86), (0.56, 0.82),
      (0.64, 0.84), (0.70, 0.9), (0.76, 1.0), (1.0, 1.0)]
# profundidad del tronco (sobre y=0)
SY = [(-0.9, 1.0), (0.0, 1.0), (0.12, 0.96), (0.22, 0.9), (0.32, 0.95), (0.55, 0.95),
      (0.7, 0.92), (0.78, 1.0), (1.0, 1.0)]
# grosor de pierna alrededor de su eje
GL = [(-0.9, 0.96), (-0.6, 0.94), (-0.5, 0.97), (-0.35, 1.04), (-0.15, 1.07), (0.0, 1.03)]
# grosor de brazo
GA = 0.88
# acortar tronco: z en [0, 0.62] se comprime
Z0, Z1, KZ = 0.0, 0.62, 0.94
ABD = math.radians(4.0)        # abrir brazos (abduccion) para que la mano no pise la cadera
HOMBRO = {+1: None, -1: None}


def remap_z(z):
    return np.where(z < Z0, z, np.where(z > Z1, Z0 + (Z1 - Z0) * KZ + (z - Z1), Z0 + (z - Z0) * KZ))


# articulacion del hombro por lado: centro del deltoides, algo hacia dentro
for sg in (1, -1):
    nm = "hombros_izq" if sg > 0 else "hombros_der"
    c = data[nm]
    HOMBRO[sg] = np.array([np.median(c[:, 0]) * 1.0, np.median(c[:, 1]), np.percentile(c[:, 2], 70)])
print("hombros", HOMBRO)
sx_h = float(interp(HOMBRO[1][2], SX))
dz_h = float(remap_z(np.array([HOMBRO[1][2]]))[0] - HOMBRO[1][2])


def gauss(co, c, s):
    d = (co - np.array(c)) / np.array(s)
    return np.exp(-0.5 * (d ** 2).sum(1))


def deforma_tronco(co):
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    out = np.empty_like(co)
    out[:, 0] = x * interp(z, SX)
    out[:, 1] = y * interp(z, SY)
    out[:, 2] = remap_z(z)
    return out


def relieves(co):
    """Desplazamientos aditivos (pecho y gluteo), iguales para tronco, pierna y brazo."""
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    d = np.zeros_like(co)
    for sg in (1, -1):
        g = gauss(co, (sg * 0.105, -0.11, 0.445), (0.065, 0.07, 0.06)) * ss(0.02, -0.06, y)
        d[:, 1] -= 0.042 * g
        d[:, 2] -= 0.012 * g
        d[:, 0] += sg * 0.008 * g
        g2 = gauss(co, (sg * 0.075, 0.11, -0.05), (0.075, 0.07, 0.09)) * ss(0.0, 0.07, y)
        d[:, 1] += 0.024 * g2
    return d


def deforma_pierna(co):
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    sg = np.where(x >= 0, 1, -1)
    cx = np.empty_like(x); cy = np.empty_like(y)
    for s in (1, -1):
        m = sg == s
        cx[m], cy[m] = eje(EJE_PIERNA, s, z[m])
    g = interp(z, GL)
    out = np.empty_like(co)
    out[:, 0] = cx * interp(z, SX) + (x - cx) * g
    out[:, 1] = cy + (y - cy) * g
    out[:, 2] = z
    return out


def deforma_brazo(co):
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    sg = np.where(x >= 0, 1, -1)
    out = np.empty_like(co)
    for s in (1, -1):
        m = sg == s
        cx, cy = eje(EJE_BRAZO, s, z[m])
        # adelgazar alrededor del eje
        px = cx + (x[m] - cx) * GA
        py = cy + (y[m] - cy) * GA
        pz = z[m]
        # abduccion alrededor del hombro (eje Y)
        H = HOMBRO[s]
        rx, rz = px - H[0], pz - H[2]
        a = s * ABD
        # el brazo cuelga (rz<0): girar para alejar la mano del tronco
        qx = rx * math.cos(a) - rz * math.sin(a)
        qz = rx * math.sin(a) + rz * math.cos(a)
        out[m, 0] = H[0] * sx_h + qx
        out[m, 1] = py
        out[m, 2] = H[2] + dz_h + qz
    return out


res = {}
for o in objs:
    co = data[o.name]
    wa = W[o.name][:, None]; wl = WL[o.name][:, None]
    t = deforma_tronco(co)
    l = deforma_pierna(co)
    a = deforma_brazo(co)
    wt = np.clip(1 - wa - wl, 0, 1)
    res[o.name] = t * wt + l * wl + a * wa + relieves(co) * (1 - wa)

allc = np.concatenate(list(res.values()))
mn, mx = allc.min(0), allc.max(0)
s = ALTURA / (mx[2] - mn[2])
centro = (mn + mx) / 2
print("alto antes de escalar", mx[2] - mn[2], "escala", s)

for o in objs:
    co = (res[o.name] - centro) * s
    M = np.array(o.matrix_world)
    Minv = np.linalg.inv(M)
    loc = co @ Minv[:3, :3].T + Minv[:3, 3]
    o.data.vertices.foreach_set("co", loc.astype(np.float32).ravel())
    o.data.update()

# comprobar holgura mano-cadera
allf = {o.name: (res[o.name] - centro) * s for o in objs}
for sg in (1, -1):
    mano = np.concatenate([allf[o.name][(W[o.name] > 0.9) & (np.sign(data[o.name][:, 0]) == sg)] for o in objs])
    cuerpo = np.concatenate([allf[o.name][(W[o.name] < 0.1) & (np.sign(data[o.name][:, 0]) == sg)] for o in objs])
    zz = mano[:, 2]
    worst = 9
    for z in np.arange(zz.min(), min(zz.max(), 0.1), 0.02):
        a = mano[np.abs(mano[:, 2] - z) < 0.01]; b = cuerpo[np.abs(cuerpo[:, 2] - z) < 0.01]
        if len(a) and len(b):
            gap = (np.abs(a[:, 0]).min() - np.abs(b[:, 0]).max())
            worst = min(worst, gap)
    print("holgura minima brazo-tronco lado", sg, round(float(worst), 4))

for o in bpy.context.scene.objects:
    o.select_set(o.type == "MESH")
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_yup=True,
                          export_extras=True, export_materials="EXPORT", export_animations=False,
                          export_cameras=False, export_lights=False)
print("OK", OUT)
