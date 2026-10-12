import geopandas as gpd
import rioxarray
from shapely.geometry import mapping


def recortar_pm25_por_cidade(caminho_nc, caminho_gpkg, caminho_saida_tif):
    """Recorta um arquivo NetCDF de PM2.5 usando o limite geométrico de um GeoPackage.

    Salva o resultado em formato GeoTIFF.
    """
    print("⏳ Carregando o vetor da cidade (GPKG)...")
    # 1. Carrega o arquivo GPKG da cidade
    cidade_gdf = gpd.read_file(caminho_gpkg)

    print("⏳ Carregando o arquivo de satélite (NetCDF)...")
    # 2. Abre o arquivo NetCDF usando o rioxarray
    # Nota: Substitua 'PM25' pelo nome exato da variável de dados dentro do seu arquivo .nc se necessário
    dados_nc = rioxarray.open_rasterio(caminho_nc)

    # 3. Garante que os dados do NetCDF possuem um CRS (Sistema de Coordenadas) definido.
    # O padrão do produto ACAG van Donkelaar é WGS84 (EPSG:4326)
    if dados_nc.rio.crs is None:
        dados_nc = dados_nc.rio.write_crs("EPSG:4326")

    # 4. Garante que o GPKG da cidade esteja na mesma projeção/CRS do arquivo NetCDF
    if cidade_gdf.crs != dados_nc.rio.crs:
        print(f"🔄 Reprojetando a cidade de {cidade_gdf.crs} para {dados_nc.rio.crs}...")
        cidade_gdf = cidade_gdf.to_crs(dados_nc.rio.crs)

    print("✂️ Executando o recorte da camada...")
    # 5. Corta o raster usando a geometria da cidade
    # 'all_touched=True' garante que pixels que tocam a borda da cidade também sejam incluídos
    raster_recortado = dados_nc.rio.clip(
        cidade_gdf.geometry.apply(mapping),
        cidade_gdf.crs,
        all_touched=True,
        drop=True,
    )

    print(f"💾 Salvando o resultado em: {caminho_saida_tif}")
    # 6. Salva o arquivo recortado em formato GeoTIFF (fácil de abrir no QGIS ou ArcGIS)
    raster_recortado.rio.to_raster(caminho_saida_tif)
    print("✅ Processo concluído com sucesso!")


# --- CONFIGURAÇÃO DOS CAMINHOS ---
# Altere os caminhos abaixo com os nomes dos seus arquivos locais
ARQUIVO_NC = r"C:\Users\mateu\OneDrive\Desktop\NO2 e PM2.5\PM2.5\.nc\V6GL02.04.CNNPM25.GL.202301-202312.nc"
ARQUIVO_GPKG = r"gpkg\RMF.gpkg"
ARQUIVO_SAIDA = "pm25_RMF_2023.tif"

# Executa a função
recortar_pm25_por_cidade(ARQUIVO_NC, ARQUIVO_GPKG, ARQUIVO_SAIDA)
