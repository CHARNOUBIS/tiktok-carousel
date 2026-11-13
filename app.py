import streamlit as st
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
import json
import os
import io
import requests
import urllib.parse

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="TikTok Shop Carousel Studio", layout="wide")
st.title("🛒 Générateur Automatique de Carrousels TikTok Shop")

# --- BARRE LATÉRALE : CLÉS API ---
with st.sidebar:
    st.header("⚙️ Configuration")
    raw_api_key = st.text_input("Clé API Google Gemini", type="password")
    # Nettoyage automatique des espaces invisibles ajoutés par le clavier mobile
    gemini_api_key = raw_api_key.strip() if raw_api_key else ""
    
    moteur_image = st.selectbox(
        "Moteur de génération Photo",
        ["Gratuit Illimité (Flux Realism)", "Google Imagen 3 (Nécessite Facturation Google)"]
    )
    tiktok_access_token = st.text_input("Token API TikTok (Optionnel)", type="password")

# --- FONCTION : INCRUSTATION DU TEXTE STYLE TIKTOK NATIF ---
def add_tiktok_text(image_bytes, top_text, bottom_text):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
    
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
    except:
        font = ImageFont.load_default()

    def draw_text_box(text, y_pos):
        if not text:
            return
        words = text.split()
        lines, current_line = [], ""
        for word in words:
            if len(current_line + " " + word) <= 30:
                current_line += (" " + word if current_line else word)
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        line_height = 62
        box_height = len(lines) * line_height + 40
        box_width = 960
        x_box = (1080 - box_width) // 2

        draw.rounded_rectangle(
            [x_box, y_pos, x_box + box_width, y_pos + box_height],
            radius=25,
            fill=(0, 0, 0, 200)
        )

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
            x_text = (1080 - text_w) // 2
            draw.text((x_text, y_pos + 20 + i * line_height), line, font=font, fill=(255, 255, 255, 255))

    draw_text_box(top_text, 180)
    draw_text_box(bottom_text, 1380)

    final_img = Image.alpha_composite(img, overlay).convert("RGB")
    return final_img

# --- INTERFACE PRINCIPALE ---
uploaded_file = st.file_uploader("📸 Glisse ta capture d'écran de produit TikTok Shop ici", type=["jpg", "jpeg", "png"])

if uploaded_file and st.button("🚀 Générer le Carrousel Complet (6 Slides)"):
    if not gemini_api_key:
        st.error("⚠️ Renseigne ta clé API Gemini dans le menu en haut à gauche (la petite flèche >).")
        st.stop()

    try:
        client = genai.Client(api_key=gemini_api_key)
        product_img = Image.open(uploaded_file).convert("RGB")

        with st.spinner("1/2 - Analyse de la capture d'écran et rédaction du script PAS..."):
            prompt_analyse = """
            Tu es un expert TikTok Shop France. Analyse cette capture d'écran de produit et retourne UNIQUEMENT un objet JSON valide avec cette structure exacte :
            {
              "titre_accrocheur": "Titre court et viral en français pour TikTok",
              "description": "Description engageante orientée conversion en français",
              "hashtags": "#tiktokshopfrance #bonplan #astuce ...",
              "description_visuelle_produit": "Detailed English visual description of the exact product packaging (colors, shape, container type, visible words) to keep consistency",
              "slides": [
                {"numero": 1, "etape": "Galère", "image_prompt": "Detailed English prompt for a raw candid iPhone photo 9:16 showing the problem", "texte_haut": "Texte choc haut en français", "texte_bas": "Texte choc bas en français"},
                {"numero": 2, "etape": "Agitation", "image_prompt": "Detailed English prompt...", "texte_haut": "...", "texte_bas": "..."},
                {"numero": 3, "etape": "Découverte", "image_prompt": "Detailed English prompt...", "texte_haut": "...", "texte_bas": "..."},
                {"numero": 4, "etape": "Démonstration", "image_prompt": "Detailed English prompt...", "texte_haut": "...", "texte_bas": "..."},
                {"numero": 5, "etape": "Transformation", "image_prompt": "Detailed English prompt...", "texte_haut": "...", "texte_bas": "..."},
                {"numero": 6, "etape": "CTA", "image_prompt": "Detailed English prompt...", "texte_haut": "...", "texte_bas": "..."}
              ]
            }
            Sur les slides 3, 4, 5 et 6, intègre systématiquement la 'description_visuelle_produit' dans 'image_prompt'.
            """

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[product_img, prompt_analyse],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(response.text)
            st.session_state["carousel_data"] = data

        os.makedirs("output_carousel", exist_ok=True)
        generated_images_bytes = []

        with st.spinner("2/2 - Génération des 6 photos dans l'ordre et ajout des textes TikTok..."):
            for idx, slide in enumerate(data["slides"]):
                full_prompt = f"Raw candid iPhone photo, authentic UGC style, vertical 9:16, natural indoor lighting, no text in background: {slide['image_prompt']}"
                
                if "Gratuit" in moteur_image:
                    encoded_prompt = urllib.parse.quote(full_prompt)
                    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&model=flux-realism&nologo=true&seed={idx+42}"
                    res = requests.get(url, timeout=60)
                    raw_bytes = res.content
                else:
                    img_result = client.models.generate_images(
                        model="imagen-3.0-generate-002",
                        prompt=full_prompt,
                        config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="9:16")
                    )
                    raw_bytes = img_result.generated_images[0].image.image_bytes

                final_pil = add_tiktok_text(raw_bytes, slide["texte_haut"], slide["texte_bas"])
                
                buf = io.BytesIO()
                final_pil.save(buf, format="JPEG", quality=95)
                img_bytes = buf.getvalue()
                generated_images_bytes.append((slide["numero"], slide["etape"], img_bytes))

            st.session_state["generated_images"] = generated_images_bytes

    except Exception as e:
        st.error(f"❌ Détail exact de l'erreur : {str(e)}")
        st.info("💡 Vérifie que ta clé API Gemini est bien copiée en entier depuis aistudio.google.com (commence généralement par 'AIza...').")

# --- AFFICHAGE DU COPYWRITING ET TÉLÉCHARGEMENT MOBILE ---
if "carousel_data" in st.session_state:
    data = st.session_state["carousel_data"]
    st.subheader("📝 Copywriting Prêt à Copier-Coller")
    st.text_input("Titre Accrocheur", value=data["titre_accrocheur"])
    st.text_area("Description & Tags", value=f"{data['description']}\n\n{data['hashtags']}", height=120)

if "generated_images" in st.session_state:
    st.subheader("📸 Tes 6 Photos Ordonnées (1 à 6)")
    for num, etape, img_bytes in st.session_state["generated_images"]:
        st.image(img_bytes, caption=f"Slide {num} - {etape}", use_container_width=True)
        st.download_button(
            label=f"📥 Télécharger Slide {num} ({etape})",
            data=img_bytes,
            file_name=f"Slide_{num}.jpg",
            mime="image/jpeg",
            key=f"dl_{num}"
        )
