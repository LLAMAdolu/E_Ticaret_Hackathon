import streamlit as st
from PIL import Image, ImageDraw, ImageOps
import requests
from io import BytesIO
from tempfile import NamedTemporaryFile
from streamlit_image_select import image_select
from services import UserService
import time  # Bu satırı ekledik
import sys
import os

# VisionModel dizininin mutlak yolunu alıyoruz
vision_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'VisionModel'))
# Bu yolu Python arama yoluna ekliyoruz
if vision_model_path not in sys.path:
    sys.path.append(vision_model_path)
from image_processing_pipeline import process_image_pipeline

user_service = UserService()

# Uygulama arka plan stilini belirle
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), 
                    url("https://www.gidamuhendisleri.org.tr/wp-content/uploads/2021/08/organik_gida_ihracat-1-1110x628.jpg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Oturum durumları için varsayılan değerleri ayarla
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'navigation_initialized' not in st.session_state:
    st.session_state['navigation_initialized'] = False

if 'users' not in st.session_state:
    st.session_state['users'] = {}  # Basit bir kullanıcı veritabanı

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
    st.title("Login Ekranı")

    # Kullanıcı adı ve şifre giriş alanları
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    
    # İki sütun (Giriş ve Kayıt ol butonları için)
    col1, col2 = st.columns(2)
    
    # CSS ile sağ kolonu hizala
    st.markdown(
        """
        <style>
            div[data-testid="column"]:nth-of-type(2) { text-align: end; } 
        </style>
        """, unsafe_allow_html=True
    )

    # Giriş butonu (Sol kolon)
    with col1:
        if st.button("Giriş"):
            # Kullanıcı doğrulama işlemi
            if user_service.check_login(username, password):
                st.success(f"Başarıyla giriş yaptınız!")
                st.session_state.page = 1  # Başarıyla giriş yapıldıysa ana sayfaya yönlendir
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
    st.markdown(
        """
        <style>
            div[data-testid="column"]:nth-of-type(2) { text-align: end; } 
        </style>
        """, unsafe_allow_html=True
    )

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
    st.title("Page 1: Upload Image and Input Text")

    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file

    text_input = st.text_input("Enter your text here")

    if st.button("İlerle"):
        if st.session_state.uploaded_file is None:
            st.write("Lütfen ürününüzün resim dosyasını yükleyin.")
        elif not text_input.strip():
            st.write("Lütfen ürününüz için bir açıklama yazın.")
        else:
            st.session_state.page = 2
            st.rerun()


# Sayfa 2: Yükleme işlemi ve görsel işleme.
def page_2():
    """Sayfa 2: Yüklenen resmi işleyip sonuçları gösterir."""
    st.title("Image Processing: Before and After")
    
    col1, col2 = st.columns(2)

    # Solda yüklenen dosyanın resmini göster
    with col1:
        st.subheader("Uploaded Image")
        if st.session_state.uploaded_file is not None:
            st.image(st.session_state.uploaded_file, caption="Original Image", use_column_width=True)
        else:
            st.write("Lütfen bir resim yükleyin.")

    # Sağda işlem sonrası resmi göster
    with col2:
        st.subheader("Processed Image")
        if st.session_state.uploaded_file is not None:
            # Yükleme sırasında spinner göstermek
            with st.spinner("Processing the image..."):
                # Geçici dosya oluşturma
                image = Image.open(st.session_state.uploaded_file)
                with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    image.save(temp_file.name)
                    temp_image_path = temp_file.name

                # İşleme sokulmuş resim
                processed_image = process_image_pipeline(
                    temp_image_path,
                    "Replace the background with a scene inspired by the richness of local heritage, incorporating warm, rustic tones like wooden textures or handwoven fabrics. The background should evoke a sense of tradition and authenticity, enhancing the product's connection to its roots without overpowering its appeal."
                )
                time.sleep(3)  # İşlem simülasyonu için bekleme süresi

                # İşleme sokulan resmi göster
                st.image(processed_image, caption="Processed Image", use_column_width=True)
            
        else:
            st.write("İşlenecek bir resim yükleyin.")

    # Sonraki adım butonu
    if st.button("İlerle", key="next_to_3"):
        st.session_state.page = 3
        st.rerun()



# Sayfa 3: Resim seçimi
def page_3():
    """Sayfa 3: Resim seçimi."""
    st.title("Page 3: Select Image")
    
    if "images_array" not in st.session_state or st.session_state.images_array is None:
        image_urls = [
            "https://static.ticimax.cloud/cdn-cgi/image/width=540,quality=85/30523/uploads/urunresimleri/buyuk/biber-salcasi-1-kg-5-fed8.jpg",
            "https://memleketciftligi.com/1470-home_default/dogal-ev-yapimi-karisik-salca-1-kg-domates-biber-.jpg",
            "https://koylukizi.com.tr/546-home_default/kaynatma-domates-salcasi-5-kg.jpg",
            "https://memleketciftligi.com/1035-thickbox_default/dogal-karisik-koey-salcasidomates-biber-350-gr.jpg",
            "https://www.nostalji.com.tr/wp-content/uploads/2020/05/mustlukoy-1K2B6384.png",
            "https://aydinenginar.com/wp-content/uploads/2024/02/1851203_0-768x1024.jpg"
        ]

        image_paths = [
            r"Images/salca1.jpg",
            r"Images/salca2.png",
            r"Images/salca3.jpg",
            r"Images/salca4.jpg",
            r"Images/salca5.jpg",
            r"Images/salca6.jpg"
        ]

        st.session_state.images_array = [Image.open(path) for path in image_paths]

    if "selected_image" not in st.session_state:
        st.session_state.selected_image = st.session_state.images_array[0]
    
    if "images_array" in st.session_state and st.session_state.images_array:
        st.session_state.images_array[0] = raw_output_image
        st.session_state.selected_image = raw_output_image

    col1, col2 = st.columns([3, 1])
    
    with col2:
        selected_image_ = image_select(
            label="",
            images=st.session_state.images_array,
            use_container_width=True
        )
        if selected_image_:
            st.session_state.selected_image = selected_image_
    
    with col1:
        st.image(add_rounded_corners(st.session_state.selected_image.convert("RGB"), 30), caption="Selected Image", width=300)

    if st.button("İlerle", key="next_to_4"):
        st.session_state.page = 4
        st.rerun()


# Sayfa 4: Son sayfa
def page_4():
    st.title("Page 4: Final Page")
    
    col1, col2 = st.columns([3, 1])
    
    # Sol tarafta büyük resmi göster
    with col1:
        st.image(add_rounded_corners(st.session_state.selected_image.convert("RGB"),30), caption="Large Image", use_column_width=True)
    
    # Sağ tarafta text alanı göster
    with col2:
        st.subheader("Önerilen Ürün Adı ")
        st.write("Yemeğin salçalısı (Organik)")
        st.subheader("Önerilen Ürün Açıklaması")
        st.write("Mükemmel yüzde yüz organik salça. Satışını artıracak kelimelerin kullanıldığı ürün bilgisi.")
        
        # "Onayla" button at the bottom
        if st.button("Onayla"):
            st.write("You have confirmed the information.")
            # Daha fazla mantık eklenebilir (örneğin, kaydetme veya gönderme işlemleri)

# Sayfa yönlendirme
def navigation():
    col1_, col2_, col3 = st.columns([1,2,1])

    with col2_:
        current_page = st.session_state.get("page", 0)

        # CSS stilini markdown ile tanımlıyoruz
        st.markdown(
            """
            <style>
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
                background-color: #4CAF50; /* Aktif sayfa için renk */
                color: white;
            }
            .inactive {
                background-color: #343541; /* Pasif sayfalar için şeffaf */
                color: white;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Sayfa numaraları için HTML kodu oluşturuyoruz
        pages = [1, 2, 3, 4]
        page_html = ""

        for page in pages:
            if current_page == page:
                # Aktif sayfa için kutuyu renklendiriyoruz
                page_html += f'<div class="nav-box active" onclick="window.location.href=\'#{page}\'">{page}</div>'
            else:
                # Diğer sayfalar için kutular şeffaf kalacak
                page_html += f'<div class="nav-box inactive" onclick="window.location.href=\'#{page}\'">{page}</div>'

        # HTML'i sayfada render ediyoruz
        st.markdown(page_html, unsafe_allow_html=True)

        # JavaScript ile sayfa yönlendirmesi yapıyoruz
        st.markdown(
            """
            <script>
            const elements = document.querySelectorAll('.nav-box');
            elements.forEach(element => {
                element.addEventListener('click', () => {
                    const pageNumber = element.innerText;
                    window.parent.postMessage({type: "streamlit:setSessionState", sessionState: {page: parseInt(pageNumber)}}, "*");
                });
            });
            </script>
            """,
            unsafe_allow_html=True
    )
        
        
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
