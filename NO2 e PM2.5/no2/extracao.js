// 1. Carregar o seu Asset do polígono de Fortaleza
var fortaleza = ee.FeatureCollection(Fortaleza);

// 2. Chamar a coleção do TROPOMI NO2 (L3 já possui dados pré-filtrados pelo GEE)
var tropomi_bruto = ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_NO2')
  .filterDate('2023-01-01', '2023-12-31')
  .filterBounds(fortaleza);

// 3. Função de otimização e recorte
var filtrarOtimizar = function(imagem) {
  // Seleciona a densidade da coluna troposférica diretamente
  var no2_troposferico = imagem.select('tropospheric_NO2_column_number_density');
  
  return no2_troposferico.clip(fortaleza); // Recorta para otimizar o tamanho do arquivo
};

// 4. Aplicar a otimização na coleção e calcular a média anual
var colecao_filtrada = tropomi_bruto.map(filtrarOtimizar);
var media_fortaleza_2023 = colecao_filtrada.mean();

// 5. Parâmetros de visualização para conferência no mapa do GEE
var visParams = {
  min: 0.00002,
  max: 0.00015,
  palette: ['blue', 'cyan', 'green', 'yellow', 'red']
};

Map.centerObject(fortaleza, 11);
Map.addLayer(media_fortaleza_2023, visParams, 'NO2 Bruto Otimizado - Fortaleza 2023');

// 6. Exportar o dado bruto para o Google Drive
Export.image.toDrive({
  image: media_fortaleza_2023,
  description: 'TROPOMI_NO2_Bruto_Fortaleza_2023',
  scale: 1000, // Resolução aproximada em metros
  region: fortaleza.geometry(),
  fileFormat: 'GeoTIFF',
  maxPixels: 1e9
});
