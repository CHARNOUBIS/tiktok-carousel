import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import json
import io
import requests
import urllib.parse
import base64

st.set_page_config(page_title="TikTok Shop Carousel Studio", layout="wide")
st.title("🛒 Générateur Automatique de Carrousels TikTok Shop (Sans Clé API)")

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
        buf_input = io.BytesIO()
        product_img.thumbnail((800, 800))
        product_img.save(buf_input, format="JPEG", quality=85)
        b64_img = base64.b64encode(buf_input.getvalue()).decode("utf-8")

        with st.spinner("1/2 - Analyse de la capture d'écran et rédaction du script PAS..."):
            prompt_analyse = """
            Tu es un expert TikTok Shop France. Analyse cette image de produit et réponds UNIQUEMENT avec un objet JSON valide (sans balises markdown) :
            {
              "titre_accrocheur": "Titre court et viral en français",
              "description": "Description engageante orientée conversion en français",
              "hashtags": "#tiktokshopfrance #bonplan #astuce",
              "slides": [
                {"numero": 1, "etape": "Galère", "image_prompt": "Detailed English prompt for a raw candid iPhone photo 9:16 showing the daily problem solved by this product", "texte_haut": "Texte choc haut en français", "texte_bas": "Texte choc bas en français"},
                {"numero": 2, "etape": "Agitation", "image_prompt": "Detailed English prompt showing frustration with classic alternatives", "texte_haut": "Texte haut", "texte_bas": "Texte bas"},
                {"numero": 3, "etape": "Découverte", "image_prompt": "Detailed English prompt of a person holding the exact product packaging from the screenshot", "texte_haut": "Texte haut", "texte_bas": "Texte bas"},
                {"numero": 4, "etape": "Démonstration", "image_prompt": "Detailed English prompt showing the product in use", "texte_haut": "Texte haut", "texte_bas": "Texte bas"},
                {"numero": 5, "etape": "Transformation", "image_prompt": "Detailed English prompt showing the positive result and happy person", "texte_haut": "Texte haut", "texte_bas": "Texte bas"},
                {"numero": 6, "etape": "CTA", "image_prompt": "Detailed English prompt of the product packaging close-up with person smiling", "texte_haut": "Texte haut avec le prix", "texte_bas": "Clique sur le panier orange en bas à gauche !"}
              ]
            }
            """
            payload = {
                "model": "openai",
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_analyse},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                        ]
                    }
                ]
            }
            res_text = requests.post("https://text.pollinations.ai/openai", json=payload, timeout=60)
            content_str = res_text.json()["choices"][0]["message"]["content"]
            content_str = content_str.replace("```json", "").replace("```", "").strip()
            data = json.loads(content_str)
            st.session_state["carousel_data"] = data

        generated_images_bytes = []
        with st.spinner("2/2 - Génération des 6 photos dans l'ordre..."):
            for idx, slide in enumerate(data["slides"]):
                full_prompt = f"Raw candid iPhone photo, authentic UGC style, vertical 9:16, natural indoor lighting: {slide['image_prompt']}"
                encoded_prompt = urllib.parse.quote(full_prompt)
                url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&model=flux-realism&nologo=true&seed={idx+100}"
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
