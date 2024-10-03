import streamlit as st
from PIL import Image, ImageDraw, ImageOps, ImageEnhance
import requests
from io import BytesIO
from tempfile import NamedTemporaryFile
from streamlit_image_select import image_select
from db_service import UserService, ProductService
import time 
import sys
import os
import products


# VisionModel dizininin mutlak yolunu alıyoruz
vision_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'VisionModel'))
# Bu yolu Python arama yoluna ekliyoruz
if vision_model_path not in sys.path:
    sys.path.append(vision_model_path)
    
from image_processing_pipeline import process_image_pipeline
user_service = UserService()
product_service = ProductService()

# Dil seçenekleri
language_options = ['Türkçe', 'English']

# Sidebar'da dil seçme mekanizması ekle
if 'language' not in st.session_state:
    st.session_state.language = 'Türkçe'

# Dil seçimi
st.sidebar.subheader("Dil Seçin / Choose Language")
selected_language = st.sidebar.selectbox("Dil / Language", language_options)

# Dil seçimi değişirse session state'i güncelle
if selected_language != st.session_state.language:
    st.session_state.language = selected_language
    st.rerun()

st.markdown(
    """
    <style>
    .bg-image {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.7)), 
                    url("https://www.gidamuhendisleri.org.tr/wp-content/uploads/2021/08/organik_gida_ihracat-1-1110x628.jpg");        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        filter: blur(15px);
        z-index: -1;
    }

    /* İçeriği ön planda tutmak için */
    .stApp {
        z-index: 0;
    }
    </style>
    <div class="bg-image"></div>
    """,
    unsafe_allow_html=True
)

if 'product_list' not in st.session_state:
    st.session_state['product_list'] = [
    {"name": "Ürün 1", "image": Image.open("Images/salca6.jpg"), "description": "Ürün 1 hakkında detaylı bilgi."},
    {"name": "Ürün 2", "image": Image.open("Images/salca6.jpg"), "description": "Ürün 2 hakkında detaylı bilgi."},
    {"name": "Ürün 3", "image": Image.open("Images/salca6.jpg"), "description": "Ürün 3 hakkında detaylı bilgi."},
    {"name": "Ürün 4", "image": Image.open("Images/salca6.jpg"), "description": "Ürün 4 hakkında detaylı bilgi."},
    {"name": "Ürün 5", "image": Image.open("Images/salca6.jpg"), "description": "Ürün 5 hakkında detaylı bilgi."},
    {"name": "Ürün 6", "image": Image.open("Images/salca6.jpg"), "description": "Ürün 6 hakkında detaylı bilgi."},
]

FASTAPI_URL = "http://localhost:8000/process-image/"

def call_inpainting_service(image_path, prompt):
    with open(image_path, "rb") as img_file:
        files = {'input_image': img_file}
        data = {'prompt': prompt}

        # Make the POST request to the FastAPI service
        response = requests.post(FASTAPI_URL, files=files, data=data)

        # Hata mesajı ve yanıt kontrolü
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code} - {response.text}")
        
        try:
            # Yanıtın doğrudan ham verisini okuma
            image = Image.open(BytesIO(response.content))
            return image
        except Exception as e:
            raise Exception(f"Error opening the processed image: {e}")

# Oturum durumları için varsayılan değerleri ayarla
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""
    
if 'page' not in st.session_state:
    st.session_state.page = "login"

if 'navigation_initialized' not in st.session_state:
    st.session_state['navigation_initialized'] = False

if 'users' not in st.session_state:
    st.session_state['users'] = {}  # Basit bir kullanıcı veritabanı
    
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = -1
    
if 'improved_header' not in st.session_state:
    st.session_state['improved_header'] = ""
    
if 'improved_desc' not in st.session_state:
    st.session_state['improved_desc'] = ""
    
if 'image_path' not in st.session_state:
    st.session_state['image_path'] = ""

# Yardımcı fonksiyonlar
def load_image_from_url(url):
    """URL'den resim indirip PIL Image nesnesine dönüştürür."""
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img

def add_rounded_corners(image, radius):
    """Görselin köşelerini yuvarlar."""
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0) + image.size, radius=radius, fill=255)
    output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    return output

# Görsellerin varsayılanı
raw_output_image = load_image_from_url("https://platincdn.com/3094/pictures/DPOFTDYUOC818202119498_YQSMKACAXY91220209418_ev-yapimi-domates-salcasi-an.jpg")

# Giriş fonksiyonu
def login():
    """Kullanıcı giriş ekranı."""
    st.title("Giriş Yap")

    # Kullanıcı adı ve şifre giriş alanları
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    
    # Bootstrap CSS link
    st.markdown("""
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    """, unsafe_allow_html=True)
    
    
    # İki sütun (Giriş ve Kayıt ol butonları için)
    col1, col2 = st.columns(2)

    # Giriş butonu (Sol kolon)
    with col1:
        if st.button("Giriş"):
            # Kullanıcı doğrulama işlemi
            logged, user_id = user_service.check_login(username, password)
            if logged:
                st.session_state['logged_in'] = True
                st.success(f"Başarıyla giriş yaptınız!")
                st.session_state.page = 1  # Başarıyla giriş yapıldıysa ana sayfaya yönlendir
                st.session_state['user_id'] = user_id
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre yanlış")
            
    # Kayıt ol butonu (Sağ kolon)
    with col2:
        if st.button("Kayıt Ol"):
            st.session_state.page = 'register'  # Kayıt sayfasına yönlendir
            st.rerun()

def register():
    st.title("Kayıt Ol")
    
    # Bootstrap CSS link
    st.markdown("""
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    """, unsafe_allow_html=True)


    # Kullanıcı adı, şifre ve şehir bilgisi giriş kutuları
    new_username = st.text_input("Yeni Kullanıcı Adı")
    new_password = st.text_input("Yeni Şifre", type="password")
    confirm_password = st.text_input("Şifreyi Onaylayın", type="password")

    # Türkiye'deki 81 ili dropdown menüde göstermek için selectbox kullanıyoruz
    cities = [
        "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray", "Amasya", "Ankara", "Antalya", "Ardahan", 
        "Artvin", "Aydın", "Balıkesir", "Bartın", "Batman", "Bayburt", "Bilecik", "Bingöl", "Bitlis", "Bolu", 
        "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Düzce", "Edirne", "Elazığ", 
        "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Iğdır", 
        "Isparta", "İstanbul", "İzmir", "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri", 
        "Kırıkkale", "Kırklareli", "Kırşehir", "Kilis", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", 
        "Mardin", "Mersin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye", "Rize", "Sakarya", 
        "Samsun", "Siirt", "Sinop", "Sivas", "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", 
        "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak"
    ]

    city = st.selectbox("Şehir", cities)  # Dropdown ile şehir seçimi

    col1, col2 = st.columns(2)


    with col2:
        if st.button("Kayıt Ol"):
            if user_service.username_exists(new_username):
                st.error("Bu kullanıcı adı zaten mevcut. Lütfen başka bir kullanıcı adı seçin.")
            elif new_password != confirm_password:
                st.error("Şifreler eşleşmiyor.")
            elif not new_username or not new_password:
                st.error("Kullanıcı adı ve şifre boş bırakılamaz.")
            else:
                # Yeni kullanıcıyı kaydet, kullanıcı adı ve şifre ile birlikte şehir bilgisi de saklanıyor
                user_service.register_user(new_username, new_username, new_username, new_password, city)
                st.success(f"Kayıt başarılı! {city} şehrindensiniz. Lütfen giriş yapın.")
                st.session_state.page = 'login'  # Kayıt olduktan sonra giriş sayfasına yönlendir
                st.rerun()
    with col1:
        if st.button("Geri Dön"):
            st.session_state.page = 'login'  # Geri dön düğmesi ile login sayfasına dön
            st.rerun()


# Sayfa 1: Resim yükleme ve metin girişi
def page_1():
    """Sayfa 1: Resim yükleme ve metin girişi."""
    st.title("Adım 1: Resim Yükleme ve Açıklama Girme")

    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

    uploaded_file = st.file_uploader("Resim Yükleyin", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file

    text_input = st.text_input("Açıklamanızı Girin")

    if st.button("İlerle"):
        if st.session_state.uploaded_file is None:
            st.write("Lütfen ürününüzün resim dosyasını yükleyin.")
        elif not text_input.strip():
            st.write("Lütfen ürününüz için bir açıklama yazın.")
        else:
            st.session_state["user_input"] = text_input
            st.session_state.page = 2
            st.rerun()


# Sayfa 2: Yükleme işlemi ve görsel işleme.
def page_2():
    """Sayfa 2: Yüklenen resmi işleyip sonuçları gösterir."""
    st.title("Görüntü İyileştirme: Öncesi ve Sonrası")
    
    col1, col2, col3 = st.columns([2, 1, 2])

    # Solda yüklenen dosyanın resmini göster
    with col1:
        st.subheader("Yüklenen Fotoğraf")
        if st.session_state.uploaded_file is not None:
            st.image(st.session_state.uploaded_file, caption="Orijinal Fotoğraf", use_column_width=True)
        else:
            st.write("Lütfen bir resim yükleyin.")
            
    # Sağda işlem sonrası resmi göster
    with col3:
        st.subheader("İyileştirilmiş Resim")
        if st.session_state.uploaded_file is not None:
            # Check if processed_image is already in session state
            if 'processed_image' not in st.session_state:
                with st.spinner("Resim İyileştiriliyor..."):
                    try:
                        image = Image.open(st.session_state.uploaded_file)
                        with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                            image.save(temp_file.name)
                            temp_image_path = temp_file.name

                        # Call the FastAPI service for processing the image
                        processed_image = call_inpainting_service(
                            temp_image_path,
                            "Replace the background with a scene inspired by the richness of local heritage, incorporating warm, rustic tones like wooden textures or handwoven fabrics. The background should evoke a sense of tradition and authenticity, enhancing the product's connection to its roots without overpowering its appeal."
                        )

                        # Klasör oluştur ve dosya kaydet
                        user_id = st.session_state['user_id']  # Replace this with the actual user ID
                        folder_path = f"imgs/user_{user_id}"

                        if not os.path.exists(folder_path):
                            os.makedirs(folder_path)

                        # Mevcut dosyaları kontrol et ve uygun index bul
                        existing_files = [f for f in os.listdir(folder_path) if f.endswith("_generated.png")]
                        index = len(existing_files) + 1  # İndeksi mevcut dosyalara göre bul

                        new_filename = f"{index}_generated.png"

                        # Dosya yolunu oluştur ve kaydet
                        save_path = os.path.join(folder_path, new_filename)
                        processed_image.save(save_path)
                        st.session_state["image_path"] = str(save_path)
                        
                        # İşlenen resmi session_state'e kaydet
                        st.session_state.processed_image = processed_image

                    except Exception as e:
                        st.error(f"Error processing image: {e}")
                        st.session_state.processed_image = None

            # Display the processed image if it exists and allow further adjustments
            if st.session_state.processed_image:
                st.image(st.session_state.processed_image, caption="İyileştirilmiş Resim", use_column_width=True)
                
                # Slider for color enhancement
                sharpen_value = st.slider("Renk Keskinleştirme", 0.5, 3.0, 1.0, step=0.1)
                enhancer_color = ImageEnhance.Color(st.session_state.processed_image)
                sharpened_image = enhancer_color.enhance(sharpen_value)  # Renkleri keskinleştir

                # Slider for contrast enhancement
                contrast_value = st.slider("Kontrast Artırma", 0.5, 3.0, 1.0, step=0.1)
                enhancer_contrast = ImageEnhance.Contrast(sharpened_image)
                contrasted_image = enhancer_contrast.enhance(contrast_value)  # Kontrastı artır

                # Save the enhanced image to session state
                st.session_state.processed_image = contrasted_image
                
                # Show the final enhanced image
                st.image(st.session_state.processed_image, caption="Geliştirilmiş Resim", use_column_width=True)
            else:
                st.write("Resim işlenemedi. Lütfen tekrar deneyin.")
        else:
            st.write("İşlenecek bir resim yükleyin.")

    # "Resmi tekrar geliştir" butonu
    if st.button("Resmi tekrar geliştir", key="next_to_3"):
        st.session_state.page = 3
        st.rerun()

    # "Son adıma atla" butonu
    if st.button("Son adıma atla"):
        # Save processed image for use in page_4
        st.session_state.selected_image = st.session_state.processed_image
        st.session_state.page = 4
        st.rerun()

    # Reset butonu: Resmi ilk haline geri döndür
    if st.button("Reset"):
        st.session_state.processed_image = st.session_state.uploaded_file  # Orijinal resmi geri yükle
        st.rerun()  # Sayfayı yeniden yükleyerek slider değerlerini sıfırlayacak

# Sayfa 3: Resim seçimi
def page_3():
    """Sayfa 3: Resim seçimi."""
    st.title("Resim Seçimi: Beğendiğiniz Resmi Seçiniz")
    
    # Initialize the image selection if it hasn't been initialized yet
    if "selected_image" not in st.session_state:
        st.session_state.selected_image = st.session_state['processed_image']  # Default to processed image from page_2

    # Process the "Tekrar İşlenmiş Resim" immediately if it hasn't been processed yet
    if 'processed_image_2' not in st.session_state or st.session_state['processed_image_2'] is None:
        with st.spinner("Resim tekrar işleniyor..."):
            try:
                image = Image.open(st.session_state['uploaded_file'])
                with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    image.save(temp_file.name)
                    temp_image_path = temp_file.name

                # Call the FastAPI service for re-processing the image
                st.session_state['processed_image_2'] = call_inpainting_service(
                    temp_image_path,
                    "Replace the background with a soft, neutral-colored surface that complements the product, such as a subtle wood grain or lightly textured stone. Ensure the background is slightly blurred to keep the focus on the product, providing a warm, natural feel that enhances the product's appeal without being distracting."
                )
            except Exception as e:
                st.error(f"Error processing image: {e}")

    col1, col2 = st.columns([3, 1])

    # Sol tarafta seçilen resim
    with col1:
        st.subheader("Seçilen Resim")
        if st.session_state.selected_image:
            st.image(st.session_state.selected_image, caption="Seçilen Resim", use_column_width=True)
        else:
            st.write("Bir resim seçilmedi.")

    # Sağ tarafta üstte ilk yüklenen resmi göster
    with col2:
        st.subheader("Orijinal Yüklenen Resim")
        if 'uploaded_file' in st.session_state:
            if st.button("Bu Resmi Seç"):
                st.session_state.selected_image = st.session_state['uploaded_file']  # Set selected image
                st.rerun()
            st.image(st.session_state['uploaded_file'], caption="İlk Yüklenen Resim", use_column_width=True)
        else:
            st.write("Lütfen önce bir resim yükleyin.")

    # Sağ tarafta altta işlenmiş ikinci resmi göster
    with col2:
        st.subheader("Tekrar İşlenmiş Resim")
        if st.session_state['processed_image_2']:
            st.image(st.session_state['processed_image_2'], caption="Tekrar İyileştirilmiş Resim", use_column_width=True)
            if st.button("Bu Resmi Seç", key="processed_2_select"):
                st.session_state.selected_image = st.session_state['processed_image_2']  # Set selected image
                st.rerun()

    # İlerle butonu
    if st.button("İlerle", key="next_to_4"):
        st.session_state.page = 4
        st.rerun()


        
# Sayfa 4: Son sayfa
def page_4():
    st.title("Son Aşama")
    
    col1, col2 = st.columns([3, 1])
    
    # Sol tarafta büyük resmi göster
    with col1:
        st.image(add_rounded_corners(st.session_state.selected_image.convert("RGB"),30), caption="Resminizin Son Hali", use_column_width=True)
    
    # Sağ tarafta text alanı göster
    with col2:
        with st.spinner("Processing the text..."):
            url = "http://127.0.0.1:8000/ask-model/"

            # Define the payload (message input)
            payload = {
                "message": st.session_state["user_input"]
            }
            
            print(f"upload {payload}")
            # Send the POST request with the JSON payload
            response = requests.post(url, json=payload)

            # Check the response status code and output the response
            generated_text = ""
            if response.status_code == 200:
                generated_text = response.json()["response"]
            else:
                generated_text = f"Error: {response.status_code}, {response.text}"
            
        st.subheader("Önerilen Ürün Adı ")
        st.write(generated_text["pro_header"])
        st.subheader("Önerilen Ürün Açıklaması")
        st.write(generated_text["pro_desc"])
        
        st.session_state["improved_header"] = generated_text["pro_header"]
        st.session_state["improved_desc"] = generated_text["pro_desc"]
        
        # "Onayla" button at the bottom
        if st.button("Onayla"):
            user_id = st.session_state["user_id"]
            header_text = st.session_state["improved_header"]
            image_path = st.session_state["image_path"]
            print("SAVE PATH: " + image_path)
            description = st.session_state["improved_desc"]
            product_service.add_product(user_id, header_text, image_path, description)
            st.write("You have confirmed the information.")
            
            st.session_state.page = "My Products"  # "Ürünlerim" sayfasına yönlendirme
            st.rerun()
            
            
# Sayfa yönlendirme
def navigation():
    st.markdown(
        """
        <style>
        .nav-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
        }
        .nav-box {
            display: inline-block;
            padding: 10px 20px;
            margin: 5px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            border-radius: 10px;
            border: 2px solid #000;
            width: 50px;
            height: 50px;
        }
        .active {
            background-color: #4CAF50; /* Active page color */
            color: white;
        }
        .inactive {
            background-color: #343541; /* Inactive page color */
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Page numbers navigation bar with flexbox container
    pages = [1, 2, 3, 4]
    page_html = '<div class="nav-container">'  # Flexbox container

    for page in pages:
        if st.session_state.page == page:
            # Highlight active page
            page_html += f'<div class="nav-box active" onclick="window.location.href=\'#{page}\'">{page}</div>'
        else:
            # Inactive pages
            page_html += f'<div class="nav-box inactive" onclick="window.location.href=\'#{page}\'">{page}</div>'

    page_html += '</div>'  # Close flexbox container

    # Render the HTML for the navigation bar
    st.markdown(page_html, unsafe_allow_html=True)

     
        
# Sayfa durum kontrolü
if "page" not in st.session_state:
    st.session_state.page = 'login'

# Sayfa içeriklerini göster
if st.session_state.page == 'login':
    login()
elif st.session_state.page == 'register':
    register()
else:
    if st.session_state.page == 1:
        navigation()    
        page_1()
    elif st.session_state.page == 2:
        navigation()
        page_2()
    elif st.session_state.page == 3:
        navigation()
        page_3()
    elif st.session_state.page == 4:
        navigation()
        page_4()
    # Eğer ürünlerim sayfası seçilirse
    elif st.session_state.page == "My Products":
        products.show_products()
    elif st.session_state.page == "All Products":
        products.show_products()
    elif st.session_state.page == 'product_detail':
        products.show_product_detail()


with st.sidebar:
# CSS ile buton yazılarını sola hizalama
    st.markdown("""
    <style>
    .stButton>button {
        display: flex;
        justify-content: flex-start;  /* Buton içindeki metni sola hizalar */
        width: 100%;        /* Buton genişliğini ayarlamak için */
        margin: 0 auto;     /* Butonu ortalamak için */
    }
    </style>
    """, unsafe_allow_html=True)
    if st.button("Giriş", key = "Giriş_sidebar"):
        st.session_state.page = "login"  # Başarıyla giriş yapıldıysa ana sayfaya yönlendir
        st.rerun()
    if st.button("Ürün Ekle", key = "ÜrünEkle_sidebar"):
        if st.session_state['logged_in'] == True:
            st.session_state.page = 1  # Başarıyla giriş yapıldıysa ana sayfaya yönlendir
            st.rerun()
        else:
            st.error("Lütfen Giriş Yapınız")
    if st.button("Ürünlerim", key = "Ürünlerim_sidebar"):
        if st.session_state['logged_in'] == True:
            st.session_state.page = "My Products"  # Başarıyla giriş yapıldıysa ana sayfaya yönlendir
            st.rerun()
        else:
            st.error("Lütfen Giriş Yapınız")
    if st.button("Tüm Ürünler", key = "TümÜrünler_sidebar"):
        st.session_state.page = "All Products"  # Başarıyla giriş yapıldıysa ana sayfaya yönlendir
        st.rerun()
