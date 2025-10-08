def selectAndSaveLayers(outputGdb):
    # Get the current project and active map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    activeMap = aprx.activeMap

    if not activeMap:
        arcpy.AddError("No active map found.")
        return

    # Loop through all layers in the active map
    for layer in activeMap.listLayers():
        # Check if the layer is a feature layer
        if layer.isFeatureLayer:
            try:
                # Define output feature class name
                layerName = arcpy.ValidateTableName(layer.name, outputGdb)
                outputFeatureClass = os.path.join(outputGdb, layerName)
                arcpy.analysis.Select(layer,outputFeatureClass)

                print(f"Saved: {outputFeatureClass}")
            except Exception as e:
                print(f"Failed to process layer '{layer.name}': {e}")
    for table in activeMap.listTables():
        try:
            # Select all rows
            arcpy.management.SelectLayerByAttribute(table, "NEW_SELECTION", "1=1")

            # Create valid name for output
            tableName = arcpy.ValidateTableName(table.name, outputGdb)
            outputTable = os.path.join(outputGdb, tableName)
            arcpy.analysis.TableSelect(table, outputTable)
            print(f"Table saved: {outputTable}")
        except Exception as e:
            print(f"Failed to process table '{table.name}': {e}")


    print("Process completed.")
