import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import urllib.parse
import time

st.set_page_config(page_title="TikTok Shop Carousel Studio", layout="wide")
st.title("🛒 Générateur Automatique de Carrousels TikTok Shop")

# --- FONCTION : RÉCUPÉRER UNE IMAGE IA AVEC ANTI-BLOCAGE ---
def fetch_ai_image(prompt, seed, fallback_product_img):
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
    }
    encoded_prompt = urllib.parse.quote(prompt)
    # Utilisation de 768x1344 (format 9:16 plus rapide et qui ne plante jamais sur Pollinations)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=1344&model=flux&nologo=true&seed={seed}"
    
    for attempt in range(3):
        try:
            res = requests.get(url, headers=headers, timeout=45)
            if res.status_code == 200 and len(res.content) > 5000:
                # Vérifie que c'est bien une image valide avant de continuer
                img = Image.open(io.BytesIO(res.content)).convert("RGBA")
                return img
        except Exception:
            time.sleep(2)
            
    # Secours : si le serveur d'images est saturé, crée un fond propre avec la photo du produit
    bg = Image.new("RGBA", (1080, 1920), (25, 25, 30, 255))
    prod_copy = fallback_product_img.copy().convert("RGBA")
    prod_copy.thumbnail((850, 850))
    x = (1080 - prod_copy.width) // 2
    y = (1920 - prod_copy.height) // 2
    bg.paste(prod_copy, (x, y), prod_copy)
    return bg

# --- FONCTION : INCRUSTATION DU TEXTE STYLE TIKTOK NATIF ---
def add_tiktok_text(pil_img, top_text, bottom_text, product_overlay=None):
    img = pil_img.resize((1080, 1920), Image.Resampling.LANCZOS).convert("RGBA")
    
    # Optionnel : incruste la vraie miniature du produit en bas à droite pour plus d'authenticité
    if product_overlay is not None:
        thumb = product_overlay.copy().convert("RGBA")
        thumb.thumbnail((320, 320))
        img.paste(thumb, (1080 - thumb.width - 50, 960), thumb)

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

# --- INTERFACE PRINCIPALE ---
uploaded_file = st.file_uploader("📸 Glisse ta capture d'écran de produit TikTok Shop ici", type=["jpg", "jpeg", "png"])
nom_produit = st.text_input("✏️ Nom ou type du produit (ex: Créatine OstroVit, Duo Medicube...)", placeholder="Optionnel : aide à personnaliser le texte")

if uploaded_file and st.button("🚀 Générer le Carrousel Complet (6 Slides)"):
    product_img = Image.open(uploaded_file).convert("RGB")
    sujet = nom_produit.strip() if nom_produit.strip() else "ce produit viral"

    data = {
        "titre_accrocheur": f"Pourquoi tout le monde s'arrache {sujet} sur TikTok ! 🔥",
        "description": f"J'ai enfin testé {sujet} et la différence est incroyable dès les premiers jours. Dispo en promo directement dans le panier orange ci-dessous !",
        "hashtags": "#tiktokshopfrance #bonplan #astuce #viral #testproduit #pourtoi",
        "slides": [
            {
                "numero": 1,
                "etape": "Galère",
                "image_prompt": "Candid iPhone vertical photo of a tired frustrated young person looking in the mirror indoors, authentic everyday life, natural lighting",
                "texte_haut": "Mon plus gros problème depuis des mois...",
                "texte_bas": "Je cherchais une vraie solution efficace sans me ruiner."
            },
            {
                "numero": 2,
                "etape": "Agitation",
                "image_prompt": "Candid iPhone vertical photo of a person annoyed looking at cluttered products on a table at home, natural indoor lighting",
                "texte_haut": "J'avais tout essayé avant ça, mais rien ne marchait vraiment...",
                "texte_bas": "Que des promesses en l'air et de l'argent jeté par les fenêtres. ❌"
            },
            {
                "numero": 3,
                "etape": "Découverte",
                "image_prompt": "Candid iPhone vertical selfie of a smiling young person excited at home in bright daylight, authentic UGC style",
                "texte_haut": f"Puis je suis tombé sur {sujet} sur mon feed TikTok... 👀",
                "texte_bas": "Les avis étaient tellement fous que j'ai décidé de commander !"
            },
            {
                "numero": 4,
                "etape": "Démonstration",
                "image_prompt": "Candid iPhone vertical photo of hands preparing and using a daily wellness routine product on a clean counter, natural morning light",
                "texte_haut": "Ultra simple et rapide à utiliser au quotidien ✨",
                "texte_bas": "Ça prend 30 secondes et ça change complètement la donne."
            },
            {
                "numero": 5,
                "etape": "Transformation",
                "image_prompt": "Candid iPhone vertical photo of a happy confident glowing person smiling in a modern bright room, authentic UGC",
                "texte_haut": "Quelques semaines plus tard : le résultat est bluffant ! 🙌",
                "texte_bas": "Je vois enfin une vraie différence, je valide à 1000%."
            },
            {
                "numero": 6,
                "etape": "CTA",
                "image_prompt": "Candid iPhone vertical photo of a smiling person pointing downwards towards the bottom left corner of the frame, bright room",
                "texte_haut": f"🔥 {sujet} est en promo sur TikTok Shop en ce moment !",
                "texte_bas": "Clique vite sur le panier orange en bas à gauche avant la rupture ! 👇🛒"
            }
        ]
    }
    st.session_state["carousel_data"] = data

    generated_images_bytes = []
    progress_bar = st.progress(0, text="Démarrage de la génération des 6 photos...")

    for idx, slide in enumerate(data["slides"]):
        progress_bar.progress((idx) / 6, text=f"Génération de la Slide {slide['numero']}/6 ({slide['etape']})...")
        
        raw_pil = fetch_ai_image(slide["image_prompt"], seed=idx + 500, fallback_product_img=product_img)
        
        # Sur les slides 3 (Découverte) et 6 (CTA), on affiche en vignette ta capture produit pour que l'acheteur le reconnaisse
        overlay_prod = product_img if slide["numero"] in [3, 6] else None
        final_pil = add_tiktok_text(raw_pil, slide["texte_haut"], slide["texte_bas"], product_overlay=overlay_prod)
        
        buf = io.BytesIO()
        final_pil.save(buf, format="JPEG", quality=95)
        generated_images_bytes.append((slide["numero"], slide["etape"], buf.getvalue()))

    progress_bar.progress(1.0, text="✅ Tes 6 photos sont prêtes !")
    st.session_state["generated_images"] = generated_images_bytes

# --- AFFICHAGE ET TÉLÉCHARGEMENT ---
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
