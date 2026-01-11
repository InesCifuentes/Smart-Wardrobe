# Smart Wardrobe

Smart Wardrobe es un asistente de moda inteligente que analiza las prendas que subes y te sugiere combinaciones visuales según tu estilo, color, género y temporada. Su objetivo es ahorrar tiempo y dinero, maximizando el uso de tu armario y promoviendo la sostenibilidad.

El proyecto utiliza esta base de datos de prendas disponible en Kaggle:  
- https://www.kaggle.com/paramaggarwal/fashion-product-images-dataset

## Estructura del proyecto
```bash
smart-wardrobe/      
├── data/
│   └── metadata_clean.csv      # CSV limpio y preprocesado con información de las prendas
├── agents/
│   ├── image_fashion_agent.py  # Lógica del asistente de moda
│   ├── agent_prompt.py         # Prompt para el asistene
│   └── agent_messages.py       # Mensajes predefinidos del asistente
├── utils/
│   ├── dataset_utils.py        # Funciones de manejo y filtrado de metadata
│   └── filters_mapping.py      # Diccionarios de mapeo de filtros
├── vision/
│   ├── build_embeddings.py     # Script para generar los embeddings 
│   ├── clip_model.py           # Modelo CLIP
│   └── clip_similarity.py      # Funciones de CLIP
├── styles/
│   └── styles.css              # Estilos de la interfaz
├── app.py                      # Script principal de la aplicación       
├── README.md                   # Documentación
├── Dockerfile                  # Contenedor           
└── requirements.txt            # Dependencias
```

## Ejecución con Docker

Clona el repositorio:

```bash
git clone https://github.com/InesCifuentes/smart-wardrobe.git
cd smart-wardrobe
```

Construye y ejecuta el contenedor Docker:

```bash
docker build -t smart-wardrobe .
docker run -p 8501:8501 smart-wardrobe
```

Abre la app en tu navegador
- http://localhost:8501


## Uso de la aplicación

1. Configura tus filtros iniciales: género, estilo, color y estación.

2. Sube la prenda que quieras combinar.

3. El asistente mostrará sugerencias visuales y explicaciones de por qué funcionan.

4. Ajusta los filtros en cualquier momento desde la barra lateral.


## Información académica

- Escuela de Ingenierías Industrial, Informática y Aeroespacial  
- Grado en Ingeniería Informática, Sistemas de la Información y Business Intelligence  
- Inés Cifuentes Herráez