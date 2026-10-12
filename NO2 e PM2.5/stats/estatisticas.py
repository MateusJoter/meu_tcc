import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
from tqdm import tqdm

def processar_dados_espaciais(gpkg_path, entrada_dados, coluna_resultado, camada_gpkg=None, estatistica_zonal='mean'):
    
    print(f"Carregando o GeoPackage: {gpkg_path}...")
    gdf_poligonos = gpd.read_file(gpkg_path, layer=camada_gpkg)
    
    extensao = str(entrada_dados).lower()
    
    if extensao.endswith('.tif') or extensao.endswith('.tiff'):
        print(f"-> Detectado Raster (.tif). Verificando CRS e calculando estatísticas...")
        
        with rasterio.open(entrada_dados) as src:
            raster_crs = src.crs
            
            # CORREÇÃO 1: Garantir que os polígonos estejam no mesmo CRS do Raster
            if gdf_poligonos.crs != raster_crs:
                print(f"Reprojetando polígonos de {gdf_poligonos.crs} para o CRS do raster ({raster_crs})...")
                gdf_poligonos = gdf_poligonos.to_crs(raster_crs)
            
            valores = []
            # CORREÇÃO 2: Iterar com tratamento para rasters em float/nan
            for geom in tqdm(gdf_poligonos.geometry, desc="Processando Zonas (Raster)"):
                stat_result = zonal_stats(
                    [geom], 
                    src.read(1), 
                    affine=src.transform, 
                    stats=[estatistica_zonal],
                    nodata=src.nodata if src.nodata is not None else float('nan'),
                    all_touched=True  # IMPORTANTE para malhas pequenas/hexágonos: considera qualquer pixel que toque a célula
                )
                
                val = stat_result[0][estatistica_zonal] if (stat_result and stat_result[0]) else None
                valores.append(val)
                
        gdf_poligonos[coluna_resultado] = valores
        
    else:
        print(f"-> Detectado Vetor/Pontos. Calculando contagem espacial...")
        gdf_pontos = gpd.read_file(entrada_dados)
        
        if gdf_poligonos.crs != gdf_pontos.crs:
            gdf_pontos = gdf_pontos.to_crs(gdf_poligonos.crs)
        
        gdf_poligonos['_temp_id'] = range(len(gdf_poligonos))
        joined = gpd.sjoin(gdf_pontos, gdf_poligonos[['geometry', '_temp_id']], how="inner", predicate="intersects")
        contagem = joined['_temp_id'].value_counts()
        
        gdf_poligonos[coluna_resultado] = gdf_poligonos['_temp_id'].map(contagem).fillna(0).astype(int)
        gdf_poligonos = gdf_poligonos.drop(columns=['_temp_id'])

    # Salva de volta no GeoPackage
    print(f"Salvando alterações no GeoPackage...")
    gdf_poligonos.to_file(gpkg_path, layer=camada_gpkg, driver="GPKG")
    print(f"Sucesso! Nova coluna '{coluna_resultado}' salva em: {gpkg_path}")


# ==========================================
# EXEMPLO 1: Usando um Raster (.tif)
# ==========================================
processar_dados_espaciais(
    gpkg_path=r'gpkg\RMF_h3_res8.gpkg',
    entrada_dados=r'tif\pm25_RMF_2023.tif',
    coluna_resultado='pm2.5_medio_2023', # Gerenciado por você
    estatistica_zonal='mean',            # 'mean', 'max', 'min', 'sum', etc.
    camada_gpkg='H3'
)

# ==========================================
# EXEMPLO 2: Usando uma Camada de Pontos
# ==========================================
# processar_dados_espaciais(
#     gpkg_path=r'gpkg\RMF_h3_res8.gpkg',
#     entrada_dados=r'gpkg\UnidadesLogisticas2023.gpkg',
#     coluna_resultado='unidades_logisticas_2023', # Gerenciado por você
#     camada_gpkg='H3'
# )