import streamlit as st
from PIL import Image, ImageDraw, ImageOps
import requests
from io import BytesIO
import app

# Kenarları yuvarlatmak için fonksiyon
def add_rounded_corners(image, radius):
    """Görselin köşelerini yuvarlar."""
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0) + image.size, radius=radius, fill=255)
    output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    return output

# Görselleri URL'den indirip PIL nesnesine dönüştür
def load_image_from_url(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content)).convert("RGBA")  # Alpha kanalı eklemek için RGBA'ya çevir
    return img

# Ürünlerin görsellerini image formatında saklıyoruz
products = [
    {"name": "Ürün 1", "image": Image.open(r"Images/salca1.jpg"), "description": "Ürün 1 hakkında detaylı bilgi."},
    {"name": "Ürün 2", "image": Image.open(r"Images/salca1.jpg"), "description": "Ürün 2 hakkında detaylı bilgi."},
    {"name": "Ürün 3", "image": Image.open(r"Images/salca1.jpg"), "description": "Ürün 3 hakkında detaylı bilgi."},
    {"name": "Ürün 4", "image": Image.open(r"Images/salca1.jpg"), "description": "Ürün 4 hakkında detaylı bilgi."},
    {"name": "Ürün 5", "image": Image.open(r"Images/salca1.jpg"), "description": "Ürün 5 hakkında detaylı bilgi."},
    {"name": "Ürün 6", "image": Image.open(r"Images/salca1.jpg"), "description": "Ürün 6 hakkında detaylı bilgi."},
]

if 'selected_product' not in st.session_state:
    st.session_state['selected_product'] = products[0]

# Ana ürünler sayfası
def show_products():
    st.title("Ürünlerim")

    # Her üç ürünü bir satırda göstermek için döngü
    for i in range(0, len(products), 3):
        cols = st.columns(3)  # 3 sütunlu bir layout oluşturuyoruz
        
        # Sütunları ürünlerle dolduruyoruz
        for index, (col, product) in enumerate(zip(cols, products[i:i+3])):
            with col:
                # Resmi indir ve kenarlarını yuvarlat
                image = product["image"]
                rounded_image = add_rounded_corners(image, radius=100)
                
                # Ürünü görüntüle
                st.image(rounded_image, use_column_width=True)

                # Ürün ismini metin olarak göster
                st.markdown(f"<h5 style='text-align: center;'>{product['name']}</h5>", unsafe_allow_html=True)
               
                # "Ürün Detayları" butonu - Benzersiz key ile (ürün ismi + index kullanıyoruz)
                col1, col2 = st.columns([4, 1])  # Butonun olduğu sütunu daha geniş yaptık
                
                # Burada butonun genişlemesini sağlamak için st.markdown ve CSS ekliyoruz
                with col1:
                    st.markdown(
                        """
                        <style>
                        .stButton button {
                            width: 100%;
                        }
                        </style>
                        """, unsafe_allow_html=True
                    )
                    
                    if st.button("Detay", key=f"{product['name']}_{i}_{index}"):
                        st.session_state.selected_product = product
                        app.st.session_state.page = 'product_detail'
                        st.rerun()

                # İkinci sütundaki popover
                with col2:
                    st.markdown(
                        """
                        <style>
                            div[data-testid="column"]:nth-of-type(2) { text-align: right; } 
                        </style>
                        """, unsafe_allow_html=True
                    )
                    with st.popover("?"):
                        st.write(askLamadolu(product['name']))

def askLamadolu(productName):
    return "Lamadolu'ya soruldu: " + productName 



# Ürün detay sayfası
def show_product_detail():
    selected_product = st.session_state.selected_product
    st.title(selected_product["name"])

    # İki sütunlu bir layout oluşturuyoruz: Sol tarafta ürün fotoğrafı, sağ tarafta ürün adı ve açıklaması
    col1, col2 = st.columns([1, 2])

    with col1:
        # Ürün detayları - Sol sütunda ürün resmi
        st.image(selected_product["image"], use_column_width=True)
    
    with col2:
        # Sağ sütunda ürün ismi ve açıklaması
        st.markdown(f"### {selected_product['name']}")
        st.write(selected_product["description"])

    # Geri butonu
    if st.button("Geri"):
        app.st.session_state.page = 'My Products'
        app.st.rerun()

