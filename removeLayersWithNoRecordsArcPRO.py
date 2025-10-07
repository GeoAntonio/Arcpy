import arcpy

# Accede al proyecto y al mapa activo
aprx = arcpy.mp.ArcGISProject("CURRENT")
mapa = aprx.activeMap

# Recorre las capas del mapa
for capa in mapa.listLayers():
    if capa.isFeatureLayer and capa.supports("DATASOURCE"):
        try:
            count = int(arcpy.management.GetCount(capa).getOutput(0))
            if count == 0:
                # Usa supports("NAME") antes de acceder a .name
                nombre = capa.name if capa.supports("NAME") else "Capa sin nombre"
                mapa.removeLayer(capa)
                print("Capa removida:", nombre)
        except Exception as e:
            print("Error al procesar capa:", e)

del aprx
