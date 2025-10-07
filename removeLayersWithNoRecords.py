import arcpy

# Referencia al documento de mapa actual
mxd = arcpy.mapping.MapDocument("CURRENT")
df = arcpy.mapping.ListDataFrames(mxd)[0]  # Puedes ajustar si hay más de un DataFrame

# Lista de capas en el DataFrame
layers = arcpy.mapping.ListLayers(mxd, "", df)

for lyr in layers:
    # Verifica si la capa es una capa de entidad y está visible
    if lyr.isFeatureLayer:
        try:
            # Usa un cursor de búsqueda para contar registros
            count = int(arcpy.GetCount_management(lyr).getOutput(0))
            if count == 0:
                arcpy.mapping.RemoveLayer(df, lyr)
                arcpy.AddMessage("Capa removida: {}".format(lyr.name))
        except Exception as e:
            arcpy.AddWarning("No se pudo procesar la capa '{}': {}".format(lyr.name, e))

# Guarda los cambios si es necesario
# mxd.save()

del mxd
