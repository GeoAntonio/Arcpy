import arcpy
import arcgis
from arcgis.features import FeatureLayer
import pandas as pd
from typing import Optional, Dict, List, Tuple

class FeatureNavigator:
    """Navegador eficiente de features en ArcGIS Pro"""
    
    def __init__(self, layer_name: Optional[str] = None):
        """
        Inicializa el navegador
        
        Args:
            layer_name: Nombre de la capa (si None, usa la primera visible)
        """
        self.aprx = arcpy.mp.ArcGISProject("CURRENT")
        self.map = self.aprx.activeMap
        self.features = []
        self.current_index = 0
        self.current_layer = None
        self.oid_map = {}  # Mapeo rápido OID -> índice
        
        self._initialize_layer(layer_name)
    
    def _initialize_layer(self, layer_name: Optional[str]) -> None:
        """Inicializa la capa y carga los features"""
        try:
            if layer_name:
                layers = [l for l in self.map.listLayers() if l.name == layer_name]
                if not layers:
                    raise ValueError(f"Capa '{layer_name}' no encontrada")
                target_layer = layers[0]
            else:
                # Obtener primera capa de features visible
                target_layer = None
                for layer in self.map.listLayers():
                    if layer.isFeatureLayer:
                        target_layer = layer
                        break
                
                if not target_layer:
                    raise ValueError("No hay capas de features en el mapa")
            
            self.current_layer = target_layer
            self._load_features()
            print(f"✓ Capa '{self.current_layer.name}' inicializada")
            print(f"✓ {len(self.features)} registros cargados\n")
            
        except Exception as e:
            print(f"✗ Error al inicializar: {e}")
            raise
    
    def _load_features(self) -> None:
        """Carga features de forma eficiente"""
        try:
            self.features = []
            self.oid_map = {}
            
            # Obtener el data source de la capa
            datasource = self.current_layer.dataSource
            
            # Usar cursor de búsqueda para acceder a los features
            fields = ['OID@', 'SHAPE@']
            
            with arcpy.da.SearchCursor(datasource, fields) as cursor:
                for i, row in enumerate(cursor):
                    oid = row[0]
                    geometry = row[1]
                    
                    if oid is not None:
                        self.features.append({
                            'oid': oid,
                            'geometry': geometry,
                            'attributes': {'OID': oid}
                        })
                        self.oid_map[oid] = i
            
            if not self.features:
                raise ValueError("No se encontraron features con OID")
                
            self.current_index = 0
            
        except Exception as e:
            print(f"✗ Error al cargar features: {e}")
            self.features = []
    
    def pan_to_feature(self, feature: Dict) -> None:
        """Pan a un feature específico"""
        try:
            if feature['geometry']:
                # Obtener extent de la geometría
                extent = feature['geometry'].extent
                
                # Aplicar zoom con padding
                view = self.aprx.activeView
                if hasattr(view, 'camera'):
                    # Para vista 3D
                    view.camera.setExtent(extent)
                else:
                    # Para vista 2D
                    view.extent = extent
            
        except Exception as e:
            print(f"✗ Error al hacer pan: {e}")
    
    def _print_info(self) -> None:
        """Muestra información del registro actual"""
        if not self.features:
            print("✗ No hay registros cargados\n")
            return
        
        feature = self.features[self.current_index]
        total = len(self.features)
        oid = feature['oid']
        
        print(f"{'─' * 50}")
        print(f"Registro: {self.current_index + 1}/{total}")
        print(f"OID: {oid}")
        print(f"{'─' * 50}\n")
    
    def next_feature(self) -> bool:
        """Ir al siguiente feature"""
        if not self.features:
            print("✗ No hay registros cargados\n")
            return False
        
        self.current_index = (self.current_index + 1) % len(self.features)
        feature = self.features[self.current_index]
        self.pan_to_feature(feature)
        self._print_info()
        return True
    
    def previous_feature(self) -> bool:
        """Ir al feature anterior"""
        if not self.features:
            print("✗ No hay registros cargados\n")
            return False
        
        self.current_index = (self.current_index - 1) % len(self.features)
        feature = self.features[self.current_index]
        self.pan_to_feature(feature)
        self._print_info()
        return True
    
    def go_to_oid(self, oid: int) -> bool:
        """Va a un OID específico"""
        if oid not in self.oid_map:
            print(f"✗ OID {oid} no encontrado\n")
            return False
        
        self.current_index = self.oid_map[oid]
        feature = self.features[self.current_index]
        self.pan_to_feature(feature)
        self._print_info()
        return True
    
    def go_to_index(self, index: int) -> bool:
        """Va a un índice específico"""
        if index < 0 or index >= len(self.features):
            print(f"✗ Índice {index} fuera de rango (0-{len(self.features)-1})\n")
            return False
        
        self.current_index = index
        feature = self.features[self.current_index]
        self.pan_to_feature(feature)
        self._print_info()
        return True
    
    def get_current_info(self) -> Optional[Dict]:
        """Obtiene información del registro actual"""
        if not self.features:
            return None
        return self.features[self.current_index]
    
    def list_oids(self, limit: int = 50) -> None:
        """Lista OIDs disponibles"""
        if not self.features:
            print("✗ No hay registros\n")
            return
        
        print(f"{'─' * 50}")
        print(f"OIDs disponibles (mostrando {min(limit, len(self.features))}/{len(self.features)})")
        print(f"{'─' * 50}")
        
        for i in range(min(limit, len(self.features))):
            oid = self.features[i]['oid']
            marker = " ← ACTUAL" if i == self.current_index else ""
            print(f"Índice {i:4d}: OID {oid}{marker}")
        
        if len(self.features) > limit:
            print(f"\n... y {len(self.features) - limit} más")
        
        print(f"\nUsa: nav.go_to_oid(numero) o nav.go_to_index(numero)\n")
    
    def filter_by_attribute(self, field: str, value) -> List[int]:
        """Filtra features por atributo y retorna índices"""
        matches = []
        for i, feature in enumerate(self.features):
            if feature['attributes'].get(field) == value:
                matches.append(i)
        
        print(f"✓ {len(matches)} registros encontrados con {field}={value}\n")
        return matches
    
    def jump_to_filtered(self, field: str, value) -> bool:
        """Va al primer feature que cumple el filtro"""
        matches = self.filter_by_attribute(field, value)
        if matches:
            return self.go_to_index(matches[0])
        return False
    
    def export_to_dataframe(self) -> 'pd.DataFrame':
        """Exporta todos los features a un DataFrame"""
        if not self.features:
            print("✗ No hay registros\n")
            return pd.DataFrame()
        
        data = []
        for feature in self.features:
            row = feature['attributes'].copy()
            row['Índice'] = len(data)
            data.append(row)
        
        df = pd.DataFrame(data)
        print(f"✓ {len(df)} registros exportados a DataFrame\n")
        return df
    
    def get_statistics(self) -> None:
        """Muestra estadísticas de los features"""
        if not self.features:
            print("✗ No hay registros\n")
            return
        
        print(f"{'═' * 50}")
        print(f"ESTADÍSTICAS - Capa: {self.current_layer.name}")
        print(f"{'═' * 50}")
        print(f"Total de registros: {len(self.features)}")
        print(f"Registro actual: {self.current_index + 1}")
        print(f"OID actual: {self.features[self.current_index]['oid']}")
        print(f"{'═' * 50}\n")
    
    def help(self) -> None:
        """Muestra la ayuda de comandos"""
        print(f"\n{'═' * 60}")
        print("NAVEGADOR DE FEATURES - GUÍA DE COMANDOS")
        print(f"{'═' * 60}")
        print("\nNavegación:")
        print("  nav.next_feature()              Siguiente registro")
        print("  nav.previous_feature()          Registro anterior")
        print("  nav.go_to_oid(numero)           Ir a OID específico")
        print("  nav.go_to_index(numero)         Ir a índice específico")
        
        print("\nInformación:")
        print("  nav.list_oids(50)               Listar OIDs")
        print("  nav.get_current_info()          Info del registro actual")
        print("  nav.get_statistics()            Estadísticas")
        
        print("\nFiltros:")
        print("  nav.filter_by_attribute(campo, valor)")
        print("  nav.jump_to_filtered(campo, valor)")
        print("  nav.export_to_dataframe()       Exportar a DataFrame")
        
        print("\nOtros:")
        print("  nav.help()                      Mostrar esta ayuda")
        print(f"\n{'═' * 60}\n")


# ============================================================
# INICIALIZACIÓN
# ============================================================

print("\n" + "=" * 60)
print("NAVEGADOR DE FEATURES PARA ARCGIS PRO")
print("=" * 60 + "\n")

try:
    # Crear instancia global del navegador
    nav = FeatureNavigator()
    
    # Mostrar información inicial
    nav.get_statistics()
    print("Escribe: nav.help() para ver todos los comandos\n")
    
except Exception as e:
    print(f"✗ Error al inicializar: {e}")
    print("Verifica que:")
    print("  1. Tengas un mapa activo en ArcGIS Pro")
    print("  2. Haya al menos una capa de features\n")
    nav = None
