import streamlit as st
from PIL import Image, ImageDraw, ImageOps
import requests
from io import BytesIO
from db_service import ProductService, UserService
import product2map


product_service = ProductService()
user_service = UserService()
# Kenarları yuvarlatmak için fonksiyon
def add_rounded_corners(image, radius):
    """Görselin köşelerini yuvarlar."""
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0) + image.size, radius=radius, fill=255)
    output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    return output

# Ürün listesini session_state içine yükleme
if 'product_list' not in st.session_state:
    st.session_state['product_list'] = product_service.get_all_products_as_list()

# Seçilen ürünü session_state'e yükleme
if 'selected_product' not in st.session_state:
    st.session_state['selected_product'] = st.session_state.product_list[0]

def load_filtered_data():
    filter_input = st.session_state.product_filter_input
    st.session_state.product_list = product_service.get_all_products_as_list()

def show_products():
    # Dil başlığını ayarla
    st.title("Ürünlerim" if st.session_state.language == 'Türkçe' else "My Products")
    
    # Ürünleri seçilen dile göre al
    if st.session_state.language == 'Türkçe':
        products_list = product_service.get_all_products_as_list()
    else:
        products_list = product_service.get_all_products_as_english_list()
    
    # Ürünleri filtrelemek için arama kutusu
    search_label = "Ürün Ara" if st.session_state.language == 'Türkçe' else "Search Product"
    st.text_input(search_label, key="product_filter_input", on_change=load_filtered_data)

    # Her üç ürünü bir satırda göstermek için döngü
    for i in range(0, len(products_list), 3):
        cols = st.columns(3)  # 3 sütunlu bir layout oluşturuyoruz
        
        # Sütunları ürünlerle dolduruyoruz
        for index, (col, product) in enumerate(zip(cols, products_list[i:i+3])):
            with col:
                # Resmi indir ve kenarlarını yuvarlat
                image = product["image"]
                rounded_image = add_rounded_corners(image, radius=100)
                
                # Ürünü görüntüle
                st.image(rounded_image, use_column_width=True)

                # Ürün ismini metin olarak göster
                st.markdown(f"<h5 style='text-align: center;'>{product['name']}</h5>", unsafe_allow_html=True)
                
                col1_, col2_ = st.columns([4,1])
                
                with col1_:
                    # Detay buton metni dil seçimine göre değiştiriliyor
                    detail_button_text = "Detay" if st.session_state.language == 'Türkçe' else "Details"
                    
                    # "Ürün Detayları" butonu - Benzersiz key ile (ürün ismi + index kullanıyoruz)
                    if st.button(detail_button_text, key=f"{product['name']}_{i}_{index}"):
                        st.session_state['selected_product'] = product
                        st.session_state.page = 'product_detail'
                        st.rerun()
                
                with col2_:
                    # Soru işareti ikonu ile popover
                    popover_text = "?" if st.session_state.language == 'Türkçe' else "?"
                    with st.popover(popover_text):
                        st.write(askLamadolu(product['name']))

                    
def askLamadolu(productName):
    return "askLamadolu Test"
    url = "http://127.0.0.1:8000/ask-llamadolu/"
    payload = {"message": productName}
    response = requests.post(url, json=payload)
    generated_text = ""
    if response.status_code == 200:
        generated_text = response.json()["response"]
    else:
        generated_text = f"Error: {response.status_code}, {response.text}"  
    filtered_text = filter_product_description(generated_text)
    return filtered_text

# Ürün açıklamasını filtreleme fonksiyonu
def filter_product_description(output):
    # 'Product: ' ile başlayan kısmı bul ve o kısımdan itibaren metni döndür
    start_index = output.find('Product:')
    if start_index != -1:
        return output[start_index:].strip()
    else:
        return "No valid product description found."
                    
                    
# Ürün detay sayfası
def show_product_detail():
    selected_product = st.session_state['selected_product']
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
    product2map.show_city_point(user_service.get_user_region(selected_product['user']))
    # Geri butonu
    if st.button("Geri"):
        st.session_state.page = 'My Products'
        st.rerun()
