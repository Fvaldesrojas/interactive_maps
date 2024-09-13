// Variable para almacenar el ángulo de rotación en grados
var rotate_degrees = -27.3 + 90; // Por ejemplo, puedes establecer aquí el ángulo de rotación deseado
var data = {}; // Variable global para almacenar los datos GeoJSON

//IMPORTANTE INGRESAR LA API KEY DE MAPBOX PARA PODER INICIAR LA APLICACION 
// Inicializar Mapbox
var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/navigation-night-v1',
    center: [-73.06180165035789, -36.83121502282673],
    zoom: 15.2,
    bearing: rotate_degrees,
    keyboard: false,
});

map.on('load', function() {
    // Agregar una fuente de datos vacía para las características
    map.addSource('hexagonosSource', {
        type: 'geojson',
        data: {
            type: 'FeatureCollection',
            features: []
        }
    });

    // Agregar una capa para visualizar los datos
    map.addLayer({
        id: 'hexagonosLayer',
        type: 'fill', // Cambia esto a 'line' o 'circle' si es más apropiado para tus datos
        source: 'hexagonosSource',
        layout: {},
        paint: {
            // Usar una expresión condicional para determinar el color de relleno
            'fill-color': [
                'case',
                ['all', ['>=', ['get', 'path_length'], 0], ['<=', ['get', 'path_length'], 100/2]], '#00ff00',
                ['all', ['>=', ['get', 'path_length'], 100/2], ['<=', ['get', 'path_length'], 200/2]], '#33ff00',
                ['all', ['>=', ['get', 'path_length'], 200/2], ['<=', ['get', 'path_length'], 300/2]], '#55ff00',
                ['all', ['>=', ['get', 'path_length'], 300/2], ['<=', ['get', 'path_length'], 400/2]], '#77ff00',
                ['all', ['>=', ['get', 'path_length'], 400/2], ['<=', ['get', 'path_length'], 500/2]], '#99ff00',
                ['all', ['>=', ['get', 'path_length'], 500/2], ['<=', ['get', 'path_length'], 600/2]], '#bbff00',
                ['all', ['>=', ['get', 'path_length'], 600/2], ['<=', ['get', 'path_length'], 700/2]], '#ddff00',
                ['all', ['>=', ['get', 'path_length'], 700/2], ['<=', ['get', 'path_length'], 800/2]], '#ffff00',
                ['all', ['>=', ['get', 'path_length'], 800/2], ['<=', ['get', 'path_length'], 900/2]], '#ffdd00',
                ['all', ['>=', ['get', 'path_length'], 900/2], ['<=', ['get', 'path_length'], 1000/2]], '#ffbb00',
                ['all', ['>=', ['get', 'path_length'], 1000/2], ['<=', ['get', 'path_length'], 1100/2]], '#ff9900',
                ['all', ['>=', ['get', 'path_length'], 1100/2], ['<=', ['get', 'path_length'], 1200/2]], '#ff7700',
                ['all', ['>=', ['get', 'path_length'], 1200/2], ['<=', ['get', 'path_length'], 1300/2]], '#ff5500',
                ['all', ['>=', ['get', 'path_length'], 1300/2], ['<=', ['get', 'path_length'], 1400/2]], '#ff3300',
                ['all', ['>=', ['get', 'path_length'], 1400/2], ['<=', ['get', 'path_length'], 1500/2]], '#ff1100',
                '#ff0000'
            ],
            'fill-opacity': 0.8,
        }
    });  // <<-- Este es el lugar correcto para cerrar la llamada map.addLayer

    // No necesitas el paréntesis extra aquí:
    // );
1
    let socket = new WebSocket("ws://localhost:8000/ws"); // Usar IP del PC que abre el puerto

    socket.onopen = function(e) {
        console.log("[open] Conexión establecida");
    };

    socket.onmessage = function(event) {
        console.log("[message] Se ha recibido el dato geojson.");

        try {
            data = JSON.parse(event.data);
            // console.log("[message] Datos analizados:", data);

            // Actualiza los datos de la fuente de datos en el mapa con la id HexagonosSource
            if (map.getSource('hexagonosSource')) {
                map.getSource('hexagonosSource').setData(data);
            }
        } catch (error) {
            console.error("Error al analizar los datos:", error);
        }
    };

    socket.onclose = function(event) {
        if (event.wasClean) {
            console.log(`[close] Conexión cerrada limpiamente, código=${event.code} motivo=${event.reason}`);
        } else {
            console.log('[close] Conexión cerrada abruptamente');
        }
    };

}); 


