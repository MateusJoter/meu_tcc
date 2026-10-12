import geopandas as gpd
import pandas as pd

# ==========================================
# CONFIGURAÇÕES DE ENTRADA (Defina aqui)
# ==========================================
# 1. Camada de Origem (contém os dados que serão transferidos)
path_origem = r"C:\Users\mateu\OneDrive\Desktop\DadosIbge2000-2022\CE_2022.gpkg"
camada_origem = 'Ce_setores_CD2022'  # Deixe None se for um Shapefile (.shp) ou GeoJSON

# 2. Camada de Destino (vai receber a informação ponderada)
path_destino = 'gpkg\Fortaleza_h3_res8.gpkg'
camada_destino = 'Fortaleza_h3_res8'  # Deixe None se for Shapefile ou GeoJSON

# 3. Coluna numérica da origem que deseja transferir
coluna_alvo = 'Rendimento médio (responsáveis com renda positiva)'

# 4. Caminho onde o arquivo de saída será salvo
path_saida = 'gpkg\Fortaleza_h3_res8.gpkg'
camada_saida_nome = 'Fortaleza_h3_res8' # Nome da camada no arquivo de saída (se for gpkg)

# ==========================================
# PROCESSAMENTO
# ==========================================
print("Carregando as camadas...")
# Carrega origem
if camada_origem:
    gdf_origem = gpd.read_file(path_origem, layer=camada_origem)
else:
    gdf_origem = gpd.read_file(path_origem)

# Carrega destino
if camada_destino:
    gdf_destino = gpd.read_file(path_destino, layer=camada_destino)
else:
    gdf_destino = gpd.read_file(path_destino)

# Garantir que ambas estejam no mesmo CRS (idealmente projetado, ex: UTM)
if gdf_origem.crs != gdf_destino.crs:
    print(f"Reprojetando origem para o CRS do destino ({gdf_destino.crs})...")
    gdf_origem = gdf_origem.to_crs(gdf_destino.crs)

print(f"Processando interpolação por ponderação de área para a coluna '{coluna_alvo}'...")

# Atribuir um ID temporário único para cada polígono de destino
gdf_destino['_id_destino'] = range(len(gdf_destino))

# Intersecção geométrica (Overlay) para calcular as frações de área
intersecao = gpd.overlay(
    gdf_origem[['geometry', coluna_alvo]], 
    gdf_destino[['geometry', '_id_destino']], 
    how='intersection'
)

# Calcular a área de cada pedaço resultante da intersecção
intersecao['area_intersecao'] = intersecao.geometry.area

# Calcular a área total original de cada polígono de origem
gdf_origem['_area_total_origem'] = gdf_origem.geometry.area

# Mapear a área total de volta para o dataframe de intersecções usando o índice original
intersecao['_area_total_origem'] = intersecao.index.map(gdf_origem['_area_total_origem'])
intersecao['_area_total_origem'] = intersecao['_area_total_origem'].replace(0, 1)

# Cálculo ponderado: (Valor * (Área da Intersecção / Área Total do Polígono Original))
intersecao['_valor_ponderado'] = intersecao[coluna_alvo] * (intersecao['area_intersecao'] / intersecao['_area_total_origem'])

# Agrupar por polígono de destino e somar as contribuições ponderadas
valores_ponderados = intersecao.groupby('_id_destino')['_valor_ponderado'].sum().reset_index()

# Juntar o resultado de volta ao GeoDataFrame de destino
gdf_destino = gdf_destino.merge(valores_ponderados, on='_id_destino', how='left')

# Nome da nova coluna gerada
nome_nova_coluna = f"{coluna_alvo}_ponderado"
gdf_destino[nome_nova_coluna] = gdf_destino['_valor_ponderado'].fillna(0)

# Limpar colunas temporárias
gdf_destino = gdf_destino.drop(columns=['_id_destino', '_valor_ponderado'], errors='ignore')

# Salvar o resultado no arquivo de saída
print(f"Salvando o resultado em: {path_saida}...")
if path_saida.endswith('.gpkg'):
    gdf_destino.to_file(path_saida, layer=camada_saida_nome, driver="GPKG")
else:
    gdf_destino.to_file(path_saida)

print(f"Sucesso! Processo concluído. Nova coluna criada: '{nome_nova_coluna}'.")