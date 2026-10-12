import geopandas as gpd
import fiona
import libpysal
from esda.moran import Moran_Local, Moran_Local_BV

def calcular_moran_interativo(gpkg_path):
    """
    Função interativa para selecionar camadas e colunas de um GeoPackage 
    e calcular o Índice de Moran Local (Univariado ou Bivariado).
    """
    
    # 1. Listar as camadas disponíveis no GeoPackage
    try:
        camadas_disponiveis = fiona.listlayers(gpkg_path)
    except Exception as e:
        print(f"Erro ao ler o arquivo GeoPackage: {e}")
        return

    print("\n--- CAMADAS DISPONÍVEIS NO GPKG ---")
    for idx, camada in enumerate(camadas_disponiveis):
        print(f"[{idx}] {camada}")
        
    # Pergunta o número da camada
    while True:
        try:
            escolha_camada_idx = int(input("\nDigite o número correspondente à camada desejada: "))
            if 0 <= escolha_camada_idx < len(camadas_disponiveis):
                camada_escolhida = camadas_disponiveis[escolha_camada_idx]
                break
            else:
                print("Número inválido. Tente novamente.")
        except ValueError:
            print("Por favor, digite um número inteiro válido.")
            
    print(f"\nCarregando a camada '{camada_escolhida}'...")
    gdf = gpd.read_file(gpkg_path, layer=camada_escolhida)
    
    # 2. Listar as colunas disponíveis na camada
    colunas_disponiveis = [col for col in gdf.columns if col != 'geometry']
    
    print("\n--- COLUNAS DISPONÍVEIS NA CAMADA ---")
    for idx, col in enumerate(colunas_disponiveis):
        print(f"[{idx}] {col}")
        
    print("\nEscolha o tipo de análise:")
    print("[1] Univariada (Apenas 1 coluna)")
    print("[2] Bivariada (2 colunas: Coluna 1 vs Coluna 2)")
    
    tipo_analise = input("Digite 1 ou 2 para escolher o tipo de análise: ").strip()
    
    if tipo_analise == '1':
        idx_col1 = int(input("Digite o número da coluna para a análise: "))
        col1 = colunas_disponiveis[idx_col1]
        colunas = [col1]
        camada_saida = f"moran_uni_{col1}"
        
    elif tipo_analise == '2':
        idx_col1 = int(input("Digite o número da COLUNA 1: "))
        idx_col2 = int(input("Digite o número da COLUNA 2: "))
        col1 = colunas_disponiveis[idx_col1]
        col2 = colunas_disponiveis[idx_col2]
        colunas = [col1, col2]
        camada_saida = f"moran_{col1}_vs_{col2}"
    else:
        print("Opção inválida. Operação cancelada.")
        return

    # 3. Processamento do Índice de Moran (Corrigido)
    print("\nCalculando matriz de pesos espaciais (Queen)...")
    w = libpysal.weights.Queen.from_dataframe(gdf)
    w.transform = 'r' # Padronização por linha
    
    if len(colunas) == 1:
        print(f"Executando Moran Local Univariado para: '{colunas[0]}'")
        y = gdf[colunas[0]].values
        lm = Moran_Local(y, w, transformation='r', permutations=999, seed=42)
    else:
        print(f"Executando Moran Local Bivariado entre: '{colunas[0]}' vs '{colunas[1]}'")
        x = gdf[colunas[0]].values
        y = gdf[colunas[1]].values
        lm = Moran_Local_BV(x, y, w, transformation='r', permutations=999, seed=42)
        
    # Mapeamento dos quadrantes
    quadrant_labels = {1: 'H-H', 2: 'L-H', 3: 'L-L', 4: 'H-L'}
    p_vals = lm.p_sim
    q = lm.q
    
    resultados = []
    for quadrant, p in zip(q, p_vals):
        if p < 0.05:
            resultados.append(quadrant_labels.get(quadrant, 'Outros'))
        else:
            resultados.append('Não Significativo')
            
    # Atribuindo as colunas no GeoDataFrame
    gdf['Moran'] = resultados
    gdf['Moran_I_Local'] = lm.Is
    gdf['Moran_p_val'] = p_vals
    
    # 4. Salvando no GeoPackage original
    print(f"Salvando nova camada '{camada_saida}' no GeoPackage...")
    gdf.to_file(gpkg_path, layer=camada_saida, driver="GPKG")
    
    print(f"\nSucesso! Camada '{camada_saida}' salva com a coluna 'Moran' no arquivo: {gpkg_path}")

# ==========================================
# Como executar:
# ==========================================
if __name__ == "__main__":
    caminho_gpkg = r'gpkg\Fortaleza_h3_res8.gpkg'  # Substitua pelo caminho do seu arquivo
    calcular_moran_interativo(caminho_gpkg)