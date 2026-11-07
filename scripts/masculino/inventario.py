import bpy, json, sys

out = sys.argv[sys.argv.index("--") + 1]

def tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)

def walk(col, path):
    res = {"name": col.name, "path": path, "objects": [], "children": []}
    for o in col.objects:
        e = {"name": o.name, "type": o.type}
        if o.type == "MESH" and o.data:
            e["tris"] = tris(o.data)
            e["mesh"] = o.data.name
            e["mods"] = [m.type for m in o.modifiers]
        if o.parent:
            e["parent"] = o.parent.name
        res["objects"].append(e)
    for c in col.children:
        res["children"].append(walk(c, path + "/" + c.name))
    return res

sc = bpy.context.scene
data = {
    "scenes": [s.name for s in bpy.data.scenes],
    "n_objects": len(bpy.data.objects),
    "n_meshes": len(bpy.data.meshes),
    "texts": [t.name for t in bpy.data.texts][:50],
    "n_texts": len(bpy.data.texts),
    "unit_scale": sc.unit_settings.scale_length,
    "tree": walk(sc.collection, sc.collection.name),
}
with open(out, "w") as f:
    json.dump(data, f, indent=1, ensure_ascii=False)
print("OK", len(bpy.data.objects))
