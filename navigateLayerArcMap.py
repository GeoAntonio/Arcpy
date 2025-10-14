import arcpy
import pythonaddins
from threading import Timer

class NavigationTool(object):
    """Herramienta de navegación entre registros de feature class"""
    
    def __init__(self):
        self.enabled = True
        self.cursor = None
        self.current_index = 0
        self.feature_records = []
        self.layer_name = None
        self.mxd = arcpy.mapping.MapDocument("CURRENT")
        self.df = arcpy.mapping.ListDataFrames(self.mxd)[0]
        self.initialize_data()
    
    def initialize_data(self):
        """Inicializa los datos del feature class seleccionado"""
        try:
            # Obtener la primera capa visible en el mapa
            layers = arcpy.mapping.ListLayers(self.mxd, "", self.df)
            if not layers:
                pythonaddins.MessageBox("No hay capas disponibles en el mapa", "Error", 0)
                return
            
            # Usar la primera capa como ejemplo (puedes modificar esto)
            target_layer = None
            for layer in layers:
                if layer.isFeatureLayer and layer.visible:
                    target_layer = layer
                    break
            
            if not target_layer:
                pythonaddins.MessageBox("No se encontró una capa de features visible", "Error", 0)
                return
            
            self.layer_name = target_layer.name
            
            # Cargar todos los registros en memoria
            self.load_features(target_layer.dataSource)
            
            pythonaddins.MessageBox("Script inicializado. Usa 'N' para siguiente y 'B' para anterior", 
                                  "Navegación de Registros", 0)
            
        except Exception as e:
            pythonaddins.MessageBox("Error al inicializar: " + str(e), "Error", 0)
    
    def load_features(self, feature_class_path):
        """Carga todas las features en memoria"""
        try:
            self.feature_records = []
            
            # Crear cursor para leer geometrías y OIDs
            fields = ["OID@", "SHAPE@"]
            
            with arcpy.da.SearchCursor(feature_class_path, fields) as cursor:
                for row in cursor:
                    self.feature_records.append({
                        'oid': row[0],
                        'shape': row[1]
                    })
            
            if self.feature_records:
                self.current_index = 0
                pythonaddins.MessageBox("Cargados {} registros".format(len(self.feature_records)), 
                                      "Info", 0)
            else:
                pythonaddins.MessageBox("No se encontraron registros", "Advertencia", 0)
                
        except Exception as e:
            pythonaddins.MessageBox("Error al cargar features: " + str(e), "Error", 0)
    
    def pan_to_feature(self, feature_shape):
        """Hace pan a la feature especificada"""
        try:
            if feature_shape:
                # Obtener el extent de la geometría
                extent = feature_shape.extent
                
                # Hacer pan al centro de la feature
                self.df.extent = extent
                
                # Refrescar la vista
                arcpy.RefreshActiveView()
                
                # Mostrar información del registro actual
                current_record = self.feature_records[self.current_index]
                info_msg = "Registro {}/{} - OID: {}".format(
                    self.current_index + 1, 
                    len(self.feature_records),
                    current_record['oid']
                )
                
                # Mostrar mensaje temporal
                self.show_temporary_message(info_msg)
                
        except Exception as e:
            pythonaddins.MessageBox("Error al hacer pan: " + str(e), "Error", 0)
    
    def show_temporary_message(self, message):
        """Muestra un mensaje temporal en la barra de estado"""
        try:
            # Esto es una aproximación, ya que ArcMap no tiene una barra de estado fácil de acceder
            print(message)  # Se mostrará en la consola de Python
        except:
            pass
    
    def next_record(self):
        """Navega al siguiente registro"""
        if not self.feature_records:
            pythonaddins.MessageBox("No hay registros cargados", "Advertencia", 0)
            return
        
        if self.current_index < len(self.feature_records) - 1:
            self.current_index += 1
        else:
            self.current_index = 0  # Volver al principio
        
        current_feature = self.feature_records[self.current_index]
        self.pan_to_feature(current_feature['shape'])
    
    def previous_record(self):
        """Navega al registro anterior"""
        if not self.feature_records:
            pythonaddins.MessageBox("No hay registros cargados", "Advertencia", 0)
            return
        
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.feature_records) - 1  # Ir al final
        
        current_feature = self.feature_records[self.current_index]
        self.pan_to_feature(current_feature['shape'])
    
    def onKeyDown(self, event):
        """Maneja los eventos de teclado"""
        try:
            key = event.key.lower()
            
            if key == 'n':
                self.next_record()
            elif key == 'b':
                self.previous_record()
            elif key == 'r':
                # Tecla 'R' para reinicializar
                self.initialize_data()
                
        except Exception as e:
            pythonaddins.MessageBox("Error en manejo de teclas: " + str(e), "Error", 0)

# Crear instancia global de la herramienta
navigation_tool = NavigationTool()

# Función para capturar eventos de teclado
def onKeyDown(event):
    """Función global para capturar eventos de teclado"""
    navigation_tool.onKeyDown(event)

# Funciones auxiliares para usar desde la interfaz de ArcMap
def next_feature():
    """Función para ir al siguiente registro"""
    navigation_tool.next_record()

def previous_feature():
    """Función para ir al registro anterior"""
    navigation_tool.previous_record()

def reload_data():
    """Función para recargar los datos"""
    navigation_tool.initialize_data()

# Mensaje de inicio
pythonaddins.MessageBox(
    "Script de navegación cargado.\n\n" +
    "Controles:\n" +
    "- Tecla 'N': Siguiente registro\n" +
    "- Tecla 'B': Registro anterior\n" +
    "- Tecla 'R': Reinicializar datos\n\n" +
    "O usa las funciones:\n" +
    "- next_feature()\n" +
    "- previous_feature()\n" +
    "- reload_data()",
    "Navegación de Registros - Listo", 0
)

print("Script de navegación cargado. Usa 'N' para siguiente, 'B' para anterior, 'R' para reinicializar")
