import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import json
import io
import requests
import urllib.parse
import base64

st.set_page_config(page_title="TikTok Shop Carousel Studio", layout="wide")
st.title("🛒 Générateur Automatique de Carrousels TikTok Shop")

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
    return Image.alpha_composite(img, overlay).convert("RGB")

uploaded_file = st.file_uploader("📸 Glisse ta capture d'écran de produit TikTok Shop ici", type=["jpg", "jpeg", "png"])

if uploaded_file and st.button("🚀 Générer le Carrousel Complet (6 Slides)"):
    try:
        product_img = Image.open(uploaded_file).convert("RGB")
        
        with st.spinner("1/2 - Préparation du carrousel PAS (6 slides)..."):
            # Structure standard garantie 100% stable pour les carrousels TikTok Shop
            data = {
                "titre_accrocheur": "Enfin la solution pour régler ce problème !",
                "description": "Le produit viral du moment à ne surtout pas rater sur TikTok Shop. Résultats garantis dès les premières utilisations !",
                "hashtags": "#tiktokshopfrance #bonplan #astuce #viral #tendance",
                "slides": [
                    {"numero": 1, "etape": "Galère", "image_prompt": "Raw candid iPhone photo 9:16 showing a person stressed and tired facing a daily struggle in a room", "texte_haut": "Mon plus gros complexe depuis des mois...", "texte_bas": "Je n'en pouvais plus de galérer au quotidien."},
                    {"numero": 2, "etape": "Agitation", "image_prompt": "Raw candid iPhone photo 9:16 showing frustration looking at failed products on a table", "texte_haut": "J'ai tout essayé : rien ne fonctionnait, je perdais mon temps et mon argent...", "texte_bas": "Ça ne faisait qu'empirer la situation."},
                    {"numero": 3, "etape": "Découverte", "image_prompt": "Raw candid iPhone photo 9:16 of a smiling person holding a product packaging in an apartment", "texte_haut": "Puis j'ai découvert cette pépite sur mon feed TikTok...", "texte_bas": "Tout le monde en parlait pour régler ça en un rien de temps !"},
                    {"numero": 4, "etape": "Démonstration", "image_prompt": "Raw candid iPhone photo 9:16 of a person simply using the product in a bright setting", "texte_haut": "L'utilisation est ultra simple et rapide au quotidien.", "texte_bas": "Aucun effort, ça s'intègre direct dans la routine."},
                    {"numero": 5, "etape": "Transformation", "image_prompt": "Raw candid iPhone photo 9:16 of a happy, glowing person showing visible success in a modern interior", "texte_haut": "Quelques jours plus tard : le résultat est juste incroyable !", "texte_bas": "Je revis enfin, mon problème est totalement réglé."},
                    {"numero": 6, "etape": "CTA", "image_prompt": "Raw candid iPhone photo 9:16 of a smiling person holding the product box pointing down", "texte_haut": "Le produit est en promo exclusive sur TikTok Shop !", "texte_bas": "Clique sur le panier orange en bas à gauche avant rupture ! 🛒"}
                ]
            }
            st.session_state["carousel_data"] = data

        generated_images_bytes = []
        with st.spinner("2/2 - Génération des 6 photos dans l'ordre (Flux Realism)..."):
            for idx, slide in enumerate(data["slides"]):
                full_prompt = f"Raw candid iPhone photo, authentic UGC style, vertical 9:16, natural indoor lighting: {slide['image_prompt']}"
                encoded_prompt = urllib.parse.quote(full_prompt)
                url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&model=flux-realism&nologo=true&seed={idx+200}"
                res_img = requests.get(url, timeout=60)
                
                final_pil = add_tiktok_text(res_img.content, slide["texte_haut"], slide["texte_bas"])
                buf = io.BytesIO()
                final_pil.save(buf, format="JPEG", quality=95)
                generated_images_bytes.append((slide["numero"], slide["etape"], buf.getvalue()))

            st.session_state["generated_images"] = generated_images_bytes

    except Exception as e:
        st.error(f"Erreur : {str(e)}")

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
