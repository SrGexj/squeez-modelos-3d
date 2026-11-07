"""Imprime bbox y centro por malla de un GLB (coordenadas Blender, Z arriba, frente -Y)."""
import bpy, sys
import numpy as np
glb = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for o in sorted([o for o in bpy.context.scene.objects if o.type == "MESH"], key=lambda o: o.name):
    co = np.array([o.matrix_world @ v.co for v in o.data.vertices])
    print(f"{o.name:20s} min {np.round(co.min(0),3)} max {np.round(co.max(0),3)} mean {np.round(co.mean(0),3)}")
