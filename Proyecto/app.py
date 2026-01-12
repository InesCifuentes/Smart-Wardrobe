import os
import base64
from io import BytesIO
import warnings
import streamlit as st
from PIL import Image

from agents.image_fashion_agent import ImageFashionAgent
from vision.clip_similarity import search_multiple_queries, build_clip_query_generic
from utils.dataset_utils import load_metadata, get_metadata_by_id
from agents.agent_messages import AGENT_MESSAGES as messages_dict
from utils.filters_mapping import GENDER_MAP, STYLES_MAP, COLORS_MAP, SEASON_MAP

# -----------------------------
# Función para convertir PIL a base64
# -----------------------------
def pil_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

# -----------------------------
# Configuración de página
# -----------------------------
st.set_page_config(
    page_title="Smart Wardrobe",
    page_icon="💬",
    layout="wide"
)

# -----------------------------
# CSS
# -----------------------------
css_path = os.path.join("styles", "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# -----------------------------
# Cargar metadata
# -----------------------------
metadata = load_metadata("data/metadata_clean.csv")

# -----------------------------
# Inicializar session_state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "current_metadata" not in st.session_state:
    st.session_state.current_metadata = None
if "asked_combination" not in st.session_state:
    st.session_state.asked_combination = False
if "user_image_added" not in st.session_state:
    st.session_state.user_image_added = False
if "assistant_initial_message_added" not in st.session_state:
    st.session_state.assistant_initial_message_added = False
if "filters" not in st.session_state:
    st.session_state.filters = {"gender": "Any", "styles": [], "colors": [], "season": "Any"}
if "filters_set" not in st.session_state:
    st.session_state.filters_set = False

# -----------------------------
# Función para renderizar chat
# -----------------------------
def render_chat(messages):
    for msg in messages:
        content_html = ""

        # Imagen envuelta en un div para aplicar CSS
        if msg["type"] == "image":
            img_b64 = pil_to_base64(msg["content"])
            content_html += (
                f'<div class="image-container">'
                f'<img class="message-image" src="data:image/png;base64,{img_b64}">'
                f'</div>'
            )

        # Texto + caption/explanation
        caption = msg.get("caption", "")
        text_content = msg.get("content", "")
        if caption:
            content_html += f"{caption}"
        if isinstance(text_content, str) and text_content:
            if caption:
                content_html += "<br>"
            content_html += text_content

        # Determinar clase y alineación
        cls = "assistant-message" if msg["role"] == "assistant" else "user-message"
        justify = "flex-start" if msg["role"] == "assistant" else "flex-end"

        # Renderizar en Streamlit
        st.markdown(
            f'<div class="message-row" style="justify-content:{justify}">'
            f'<div class="{cls}">{content_html}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

# -----------------------------
# Encuesta inicial de filtros
# -----------------------------
if not st.session_state.filters_set:
    st.title("Smart Wardrobe", text_alignment="center")
    st.markdown(f"<div class='assistant-message'>{messages_dict['initial_filters']}</div>", unsafe_allow_html=True)
    st.markdown("")

    with st.form("initial_filters_form", border=True):
        gender_init = st.selectbox("Género", list(GENDER_MAP.keys()))
        styles_init = st.multiselect("Estilo", list(STYLES_MAP.keys()))
        colors_init = st.multiselect("Color", list(COLORS_MAP.keys()))
        season_init = st.selectbox("Estación", list(SEASON_MAP.keys()))
        submit_init = st.form_submit_button("Guardar filtros y continuar", use_container_width=True)

        if submit_init:
            st.session_state.filters = {
                "gender": GENDER_MAP[gender_init],
                "styles": [STYLES_MAP[s] for s in styles_init],
                "colors": [COLORS_MAP[c] for c in colors_init],
                "season": SEASON_MAP[season_init]
            }
            st.session_state.filters_set = True
            st.success("Filtros guardados. ¡Puedes empezar a usar el chat!")
            st.rerun()

    st.stop()

# -----------------------------
# Header del chat
# -----------------------------
st.title("Smart Wardrobe", text_alignment="center")
st.markdown(f"<div class='assistant-message'>{messages_dict['welcome_intro']}</div>", unsafe_allow_html=True)

# -----------------------------
# Sidebar de filtros ajustables (sincronizados)
# -----------------------------
with st.sidebar.form("filters_form"):
    st.sidebar.markdown("### Ajusta tus filtros")
    
    current_filters = st.session_state.filters
    
    # Mapear valores de session_state a keys para mostrar en selectbox/multiselect
    gender_val = next((k for k,v in GENDER_MAP.items() if v == current_filters.get("gender", "Any")), "Cualquiera")
    styles_val = [k for k,v in STYLES_MAP.items() if v in current_filters.get("styles", [])]
    colors_val = [k for k,v in COLORS_MAP.items() if v in current_filters.get("colors", [])]
    season_val = next((k for k,v in SEASON_MAP.items() if v == current_filters.get("season", "Any")), "Cualquiera")

    gender = st.selectbox("Género", list(GENDER_MAP.keys()), index=list(GENDER_MAP.keys()).index(gender_val))
    styles = st.multiselect("Estilo", list(STYLES_MAP.keys()), default=styles_val)
    colors = st.multiselect("Color", list(COLORS_MAP.keys()), default=colors_val)
    season = st.selectbox("Estación", list(SEASON_MAP.keys()), index=list(SEASON_MAP.keys()).index(season_val))

    submitted = st.form_submit_button("Guardar filtros")
    if submitted:
        st.session_state.filters = {
            "gender": GENDER_MAP[gender],
            "styles": [STYLES_MAP[s] for s in styles],
            "colors": [COLORS_MAP[c] for c in colors],
            "season": SEASON_MAP[season]
        }
        st.sidebar.info("Filtros guardados")

# -----------------------------
# Subida de imagen
# -----------------------------
uploaded_image = st.file_uploader(" ", type=["png", "jpg", "jpeg"])

if uploaded_image and not st.session_state.user_image_added:
    image = Image.open(uploaded_image)
    image_id = os.path.basename(uploaded_image.name).strip().lower()
    image_metadata = get_metadata_by_id(metadata, image_id)
    caption = image_metadata.get("productDisplayName", "Prenda") if image_metadata else "Prenda"

    st.session_state.current_image = image
    st.session_state.current_metadata = image_metadata
    st.session_state.asked_combination = True

    st.session_state.messages.append({
        "role": "user",
        "type": "image",
        "content": image,
        "caption": caption
    })
    st.session_state.user_image_added = True

# -----------------------------
# Mensaje inicial del asistente
# -----------------------------
if st.session_state.asked_combination and not st.session_state.assistant_initial_message_added:
    st.session_state.messages.append({
        "role": "assistant",
        "type": "text",
        "content": messages_dict["ask_combination"]
    })
    st.session_state.assistant_initial_message_added = True

# -----------------------------
# Área de input del usuario
# -----------------------------
user_input = st.chat_input("Escribe tu petición...", disabled=not st.session_state.asked_combination)

# -----------------------------
# Procesar input del usuario con warnings en lugar de exceptions
# -----------------------------
if user_input:
    st.session_state.messages.append({"role": "user", "type": "text", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "type": "text", "content": messages_dict["loading"]})

    try:
        agent = ImageFashionAgent()
        suggestions = agent.generate_suggestions(
            st.session_state.current_metadata,
            user_input,
            st.session_state.get("filters", {})
        )

        queries = [{k: v for k, v in s.items() if k != "explanation"} for s in suggestions]
        clip_results = search_multiple_queries(queries, k=1)

        # Remover mensaje temporal de "loading"
        st.session_state.messages.pop(-1)

        for s in suggestions:
            query_text = build_clip_query_generic({k: v for k, v in s.items() if k != "explanation"})
            results = clip_results.get(query_text, [])

            if results:
                r = results[0]
                clip_metadata = get_metadata_by_id(metadata, os.path.basename(r["image_path"]).strip().lower())
                caption = clip_metadata.get("productDisplayName")
                explanation_text = s.get("explanation", "Sin descripción adicional.")

                user_img_path = getattr(st.session_state.current_image, "filename", None)
                result_img_path = os.path.abspath(r["image_path"])
                if user_img_path and os.path.abspath(user_img_path) == result_img_path:
                    continue

                st.session_state.messages.append({
                    "role": "assistant",
                    "type": "image",
                    "content": Image.open(r["image_path"]),
                    "caption": f"<strong>{caption}</strong><br>{explanation_text}"
                })
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "type": "text",
                    "content": "No se encontraron resultados"
                })

        st.session_state.messages.append({
            "role": "assistant",
            "type": "text",
            "content": messages_dict["final_message"]
        })

    except Exception as e:
        warning_msg = f"⚠️ No se pudieron generar recomendaciones: {e}"
        warnings.warn(warning_msg)
        st.session_state.messages.append({
            "role": "assistant",
            "type": "text",
            "content": warning_msg
        })

# -----------------------------
# Renderizar historial completo
# -----------------------------
render_chat(st.session_state.messages)
