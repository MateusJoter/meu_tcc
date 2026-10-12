import ee

# ==========================================
# PARÂMETROS DE CONFIGURAÇÃO
# ==========================================
PROJECT_ID = 'ee-mateusjoter17'          # Substitua pelo ID do seu projeto no Google Cloud/GEE
ASSET_FORTALEZA = 'projects/ee-mateusjoter17/assets/RMF'  # Ex: 'projects/seu-projeto-id/assets/Fortaleza'
ANOS = [2023]      # Lista de anos que deseja processar
PASTA_DRIVE = 'TROPOMI_NO2_Export'     # Nome da pasta que será criada no seu Google Drive

# ==========================================
# INICIALIZAÇÃO
# ==========================================
try:
    ee.Initialize(project=PROJECT_ID)
except Exception as e:
    print("Autenticação necessária...")
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

# 1. Carregar o seu Asset do polígono de Fortaleza
fortaleza = ee.FeatureCollection(ASSET_FORTALEZA)

# 3. Função de otimização e recorte
def filtrar_otimizar(imagem):
    # Seleciona a densidade da coluna troposférica diretamente
    no2_troposferico = imagem.select('tropospheric_NO2_column_number_density')
    return no2_troposferico.clip(fortaleza.geometry()) # Recorta para otimizar o tamanho

# ==========================================
# PROCESSAMENTO ITERATIVO
# ==========================================
for ano in ANOS:
    print(f"Preparando dados para o ano {ano}...")
    
    data_inicio = f'{ano}-01-01'
    data_fim = f'{ano}-12-31'
    
    # 2. Chamar a coleção do TROPOMI NO2
    tropomi_bruto = ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_NO2') \
        .filterDate(data_inicio, data_fim) \
        .filterBounds(fortaleza)
        
    # 4. Aplicar a otimização na coleção e calcular a média anual
    colecao_filtrada = tropomi_bruto.map(filtrar_otimizar)
    media_anual = colecao_filtrada.mean()
    
    # 6. Exportar o dado bruto para o Google Drive
    descricao_tarefa = f'TROPOMI_NO2_Bruto_Fortaleza_{ano}'
    
    tarefa = ee.batch.Export.image.toDrive(
        image=media_anual,
        description=descricao_tarefa,
        folder=PASTA_DRIVE,
        scale=1000, # Resolução aproximada em metros
        region=fortaleza.geometry(),
        fileFormat='GeoTIFF',
        maxPixels=1e9
    )
    
    # Inicia a tarefa no backend do Google
    tarefa.start()
    print(f" -> Tarefa de exportação iniciada! ID: {tarefa.id}")

print("\nProcesso concluído. Todas as tarefas de exportação foram enviadas para os servidores do GEE.")
print("Você pode acompanhar o andamento no Code Editor (aba Tasks) ou aguardar os arquivos aparecerem no Drive.")