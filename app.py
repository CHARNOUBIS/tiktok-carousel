import streamlit as st
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
import json
import os
import io
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="TikTok Shop Carousel Studio", layout="wide")
st.title("🛒 Générateur Automatique de Carrousels TikTok Shop")

# --- BARRE LATÉRALE : CLÉS API ---
with st.sidebar:
    st.header("⚙️ Configuration")
    gemini_api_key = st.text_input("Clé API Google Gemini", type="password")
    tiktok_access_token = st.text_input("Token API TikTok (Optionnel)", type="password")
    st.caption("Les images sont sauvegardées automatiquement dans le dossier `./output_carousel`.")

# --- FONCTION : INCRUSTATION DU TEXTE STYLE TIKTOK NATIF ---
def add_tiktok_text(image_bytes, top_text, bottom_text):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    # Redimensionnement standard 9:16 (1080x1920)
    img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
    
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Police par défaut (Arial ou police système)
    try:
        font = ImageFont.truetype("arialbd.ttf", 46)
    except:
        font = ImageFont.load_default()

    def draw_text_box(text, y_pos):
        if not text:
            return
        # Découpage du texte en lignes de 32 caractères max
        words = text.split()
        lines, current_line = [], ""
        for word in words:
            if len(current_line + " " + word) <= 32:
                current_line += (" " + word if current_line else word)
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        line_height = 65
        box_height = len(lines) * line_height + 40
        box_width = 940
        x_box = (1080 - box_width) // 2

        # Bandeau noir semi-transparent à bords arrondis
        draw.rounded_rectangle(
            [x_box, y_pos, x_box + box_width, y_pos + box_height],
            radius=25,
            fill=(0, 0, 0, 200)
        )

        # Écriture du texte centré
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
            x_text = (1080 - text_w) // 2
            draw.text((x_text, y_pos + 20 + i * line_height), line, font=font, fill=(255, 255, 255, 255))

    draw_text_box(top_text, 180)
    draw_text_box(bottom_text, 1380)

    final_img = Image.alpha_composite(img, overlay).convert("RGB")
    return final_img

# --- INTERFACE PRINCIPALE : UPLOAD DE LA CAPTURE D'ÉCRAN ---
uploaded_file = st.file_uploader("📸 Glisse ta capture d'écran de produit TikTok Shop ici", type=["jpg", "jpeg", "png"])

if uploaded_file and st.button("🚀 Générer le Carrousel Complet (6 Slides)"):
    if not gemini_api_key:
        st.error("Renseigne ta clé API Gemini dans le menu à gauche pour démarrer.")
        st.stop()

    client = genai.Client(api_key=gemini_api_key)
    product_img = Image.open(uploaded_file)

    with st.spinner("1/2 - Analyse de la capture d'écran et rédaction du script PAS..."):
        prompt_analyse = """
        Tu es un expert TikTok Shop France. Analyse cette capture d'écran de produit et retourne UNIQUEMENT un objet JSON valide avec cette structure exacte :
        {
          "titre_accrocheur": "Titre court et viral pour TikTok",
          "description": "Description engageante orientée conversion",
          "hashtags": "#tiktokshopfrance #bonplan #astuce ...",
          "description_visuelle_produit": "Description ultra-précise du packaging/objet (couleurs, forme, texte visible) pour garder exactement le même produit sur les photos",
          "slides": [
            {"numero": 1, "etape": "Galère", "image_prompt": "Prompt photo réaliste prise à l'iPhone format 9:16 sans texte", "texte_haut": "Texte choc haut", "texte_bas": "Texte choc bas"},
            {"numero": 2, "etape": "Agitation", "image_prompt": "...", "texte_haut": "...", "texte_bas": "..."},
            {"numero": 3, "etape": "Découverte", "image_prompt": "...", "texte_haut": "...", "texte_bas": "..."},
            {"numero": 4, "etape": "Démonstration", "image_prompt": "...", "texte_haut": "...", "texte_bas": "..."},
            {"numero": 5, "etape": "Transformation", "image_prompt": "...", "texte_haut": "...", "texte_bas": "..."},
            {"numero": 6, "etape": "CTA", "image_prompt": "...", "texte_haut": "...", "texte_bas": "..."}
          ]
        }
        Sur les slides 3, 4, 5 et 6, intègre systématiquement la 'description_visuelle_produit' dans 'image_prompt' pour que le produit généré soit identique à la capture d'écran.
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[product_img, prompt_analyse],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(response.text)
        st.session_state["carousel_data"] = data

    # Création du dossier local de sortie
    os.makedirs("output_carousel", exist_ok=True)
    generated_paths = []

    with st.spinner("2/2 - Génération des 6 photos dans l'ordre et ajout des textes TikTok..."):
        cols = st.columns(6)
        for idx, slide in enumerate(data["slides"]):
            # Appel au modèle d'image Imagen 3 via l'API Gemini
            img_result = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=f"Raw candid iPhone photo, authentic UGC style, vertical 9:16, natural indoor lighting, no studio retouching: {slide['image_prompt']}",
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="9:16"
                )
            )
            raw_bytes = img_result.generated_images[0].image.image_bytes
            final_pil = add_tiktok_text(raw_bytes, slide["texte_haut"], slide["texte_bas"])
            
            file_path = f"output_carousel/Slide_{slide['numero']}.jpg"
            final_pil.save(file_path, "JPEG", quality=95)
            generated_paths.append(file_path)

            with cols[idx]:
                st.image(final_pil, caption=f"Slide {slide['numero']} - {slide['etape']}")

        st.session_state["generated_paths"] = generated_paths

# --- AFFICHAGE DU COPYWRITING ET BOUTON DE PUBLICATION ---
if "carousel_data" in st.session_state:
    data = st.session_state["carousel_data"]
    st.subheader("📝 Copywriting Prêt à Copier-Coller")
    
    st.text_input("Titre Accrocheur", value=data["titre_accrocheur"])
    st.text_area("Description & Tags", value=f"{data['description']}\n\n{data['hashtags']}", height=120)

    st.divider()
    
    if st.button("📲 Envoyer les 6 photos ordonnées sur mon compte TikTok"):
        if not tiktok_access_token:
            st.warning("⚠️ Token TikTok non renseigné : les 6 photos numérotées dans l'ordre (`Slide_1.jpg` à `Slide_6.jpg`) sont prêtes dans ton dossier `output_carousel/`.")
        else:
            # Appel à l'API officielle TikTok Content Posting (Mode Photo / Brouillon)
            headers = {
                "Authorization": f"Bearer {tiktok_access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }
            payload = {
                "post_info": {
                    "title": data["titre_accrocheur"],
                    "description": f"{data['description']} {data['hashtags']}"
                },
                "source_info": {
                    "source": "PULL_FROM_URL",
                    # Nécessite d'héberger temporairement les images ou d'utiliser le flux FILE_UPLOAD
                    "photo_cover_index": 0,
                    "photo_images": st.session_state["generated_paths"]
                },
                "post_mode": "MEDIA_UPLOAD", # Envoie directement dans les brouillons de l'application TikTok
                "media_type": "PHOTO"
            }
            res = requests.post("https://open.tiktokapis.com/v2/post/publish/content/init/", headers=headers, json=payload)
            if res.status_code == 200:
                st.success("✅ Carrousel envoyé dans tes brouillons TikTok ! Ouvre ton application mobile pour attacher le lien produit (Panier Orange) et publier.")
            else:
                st.error(f"Erreur API TikTok : {res.text}")
