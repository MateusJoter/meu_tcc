import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt

# 1. Carregar o GeoTIFF bruto exportado do Google Earth Engine
tiff_path = r'tif\TROPOMI_NO2_Bruto_Fortaleza_2023.tif'

with rasterio.open(tiff_path) as src:
    # Ler a banda de NO2 troposférico
    no2_matrix = src.read(1)
    # Copiar os metadados para salvar o arquivo final
    meta = src.meta.copy()
    # Identificar o valor usado para "Sem Dados" (NoData)
    nodata = src.nodata

# 2. Pré-processamento: Mascarar valores inválidos ou NoData
# Garantir que se nodata for None, tratemos adequadamente
if nodata is None:
    nodata_val = -9999  # Defina um valor padrão ou use np.nan se preferir
else:
    nodata_val = nodata

no2_limpo = np.where(no2_matrix == nodata_val, np.nan, no2_matrix)
mask_valid = ~np.isnan(no2_limpo)

# Para evitar vazamento das bordas nulas na filtragem, preenchemos os NaNs com 0
no2_preenchido = np.where(mask_valid, no2_limpo, 0)

# 3. Modelagem Física da Distribuição Gaussiana (Jin et al., 2025)
sigma_spatial = 2.5 
no2_oversampled = gaussian_filter(no2_preenchido, sigma=sigma_spatial)

weights = gaussian_filter(mask_valid.astype(float), sigma=sigma_spatial)
weights = np.where(weights == 0, 1, weights)

no2_final = no2_oversampled / weights
# Reaplica o nodata original (ou nan) nas bordas
no2_final = np.where(mask_valid, no2_final, np.nan)

# 4. Salvar o arquivo sobreamostrado em um novo GeoTIFF de alta qualidade
meta.update(dtype=rasterio.float32, nodata=np.nan if np.isnan(nodata_val) else nodata_val)

output_path = r'tif\no2_RMF_2023_reamostrado.tif'
with rasterio.open(output_path, 'w', **meta) as dst:
    dst.write(no2_final.astype(rasterio.float32), 1)

print(f"Oversampling concluído com sucesso! Arquivo salvo em: {output_path}")

# 5. Visualização Comparativa Rápida (com .astype(float) para evitar o erro de dtype object)
fig, ax = plt.subplots(1, 2, figsize=(12, 6))
ax[0].imshow(no2_limpo.astype(float), cmap='inferno')
ax[0].set_title('NO2 Bruto do GEE')
ax[0].axis('off')

ax[1].imshow(no2_final.astype(float), cmap='inferno')
ax[1].set_title('NO2 Sobreamostrado (Jin et al., 2025)')
ax[1].axis('off')

plt.tight_layout()
plt.show()