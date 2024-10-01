import streamlit as st
from PIL import Image, ImageDraw, ImageOps
import requests
from io import BytesIO
from streamlit_image_select import image_select

st.markdown(
    """
    <style>
    /* Arka plan görseli */
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

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'navigation_initialized' not in st.session_state:
    st.session_state['navigation_initialized'] = False

if 'users' not in st.session_state:
    st.session_state['users'] = {}  # Basit bir kullanıcı veritabanı

# Yardımcı bir fonksiyon ile URL'den resmi indir ve PIL Image nesnesine dönüştür
def load_image_from_url(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img

def add_rounded_corners(image, radius):
    # Görselin boyutlarını al
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    
    # Oval kenarlar için dairesel köşeler çiz
    draw.rounded_rectangle((0, 0) + image.size, radius=radius, fill=255)
    
    # Görsele maskeyi uygula
    output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    
    return output


raw_output_image = load_image_from_url("https://platincdn.com/3094/pictures/DPOFTDYUOC818202119498_YQSMKACAXY91220209418_ev-yapimi-domates-salcasi-an.jpg")
uploaded_file = None


# Login fonksiyonu
def login():
    st.title("Login Ekranı")

    # Kullanıcı adı ve şifre giriş kutuları
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    col1, col2 = st.columns(2)
    st.markdown(
        """
        <style>
            div[data-testid="column"]:nth-of-type(2)
            {
                text-align: end;
            } 
        </style>
        """,unsafe_allow_html=True
    )
    with col1:
        if st.button("Giriş"):
            # Basit bir doğrulama, kayıtlı kullanıcılar için kontrol (st.session_state['users'])
            if username in st.session_state['users'] and st.session_state['users'][username] == password:
                st.session_state['logged_in'] = True
                st.success("Başarıyla giriş yaptınız!")
                st.session_state.page = 1
            else:
                st.error("Kullanıcı adı veya şifre yanlış")
    with col2:
        if st.button("Kayıt Ol"):
            st.session_state.page = 'register'  # Kayıt sayfasına yönlendir

# Kayıt ol fonksiyonu
def register():
    st.title("Kayıt Ol")

    # Kullanıcı adı ve şifre giriş kutuları
    new_username = st.text_input("Yeni Kullanıcı Adı")
    new_password = st.text_input("Yeni Şifre", type="password")
    confirm_password = st.text_input("Şifreyi Onaylayın", type="password")
    col1, col2 = st.columns(2)
    st.markdown(
        """
        <style>
            div[data-testid="column"]:nth-of-type(2)
            {
                text-align: end;
            } 
        </style>
        """,unsafe_allow_html=True
    )
    with col2:
        if st.button("Kayıt Ol"):
            if new_username in st.session_state['users']:
                st.error("Bu kullanıcı adı zaten mevcut. Lütfen başka bir kullanıcı adı seçin.")
            elif new_password != confirm_password:
                st.error("Şifreler eşleşmiyor.")
            elif not new_username or not new_password:
                st.error("Kullanıcı adı ve şifre boş bırakılamaz.")
            else:
                # Yeni kullanıcıyı kaydet
                st.session_state['users'][new_username] = new_password
                st.success("Kayıt başarılı! Lütfen giriş yapın.")
                st.session_state.page = 'login'  # Kayıt olduktan sonra giriş sayfasına yönlendir
    with col1:
        if st.button("Geri Dön"):
            st.session_state.page = 'login'  # Geri dön düğmesi ile login sayfasına dön

def page_3():
    st.title("Page 3: Select Image")
    
    # Resimleri içeren array st.session_state içinde yoksa yükle
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
            
            r"C:\Users\batur\Downloads\Streamlit\Streamlit\Images\salca1.jpg",
            r"C:\Users\batur\Downloads\Streamlit\Streamlit\Images\salca2.png",
            r"C:\Users\batur\Downloads\Streamlit\Streamlit\Images\salca3.jpg",
            r"C:\Users\batur\Downloads\Streamlit\Streamlit\Images\salca4.jpg",
            r"C:\Users\batur\Downloads\Streamlit\Streamlit\Images\salca5.jpg",
            r"C:\Users\batur\Downloads\Streamlit\Streamlit\Images\salca6.jpg"
            
        ]

        # URL'lerden resimleri indir ve st.session_state içine kaydet
        #st.session_state.images_array = [load_image_from_url(url) for url in image_urls]
        st.session_state.images_array = [Image.open(path) for path in image_paths]

    # İlk elemanı varsayılan olarak seçilen resim yap
    if "selected_image" not in st.session_state:
        st.session_state.selected_image = st.session_state.images_array[0]  # İlk resim varsayılan seçili resim olacak
    
    if "images_array" in st.session_state and st.session_state.images_array:
        st.session_state.images_array[0] = raw_output_image
        st.session_state.selected_image = raw_output_image
    # Streamlit'de iki sütun oluştur
    col1, col2 = st.columns([3, 1])
    
    selected_image = None
    # Sol tarafta büyük resmi göster (300x300 boyutunda)
    # Tüm küçük resimlerden bir seçim yapılmasını sağla
    with col2:
        
        selected_image_ = image_select(
            label="",
            images=st.session_state.images_array,  # images_array'deki tüm resimleri göster
            use_container_width=True
        )
        if selected_image_:
            st.session_state.selected_image = selected_image_
    with col1:
        selected_image = st.image(add_rounded_corners(st.session_state.selected_image.convert("RGB"),30), caption="Selected Image", width=300)

    # Sonraki sayfaya geçmek için bir düğme
    if st.button("İlerle", key="next_to_4"):
        st.session_state.page = 4

# Sayfa 4 içeriği (Son sayfa)
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

# Güncellenmiş navigation fonksiyonu
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

# Sayfa 1 içeriği
def page_1():

    st.title("Page 1: Upload Image and Input Text")

    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    
    # Resim yükleme
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
    
    text_input = st.text_input("Enter your text here")
    
    if st.button("İlerle"):
        if st.session_state.uploaded_file is None:
            st.write("Lütfen ürününüzün resim dosyasını yükleyin.")
        elif text_input == None or text_input == "" or text_input == " ":
            st.write("Lütfen ürününüz için bir açıklama yazın.")
        else:
            st.session_state.page = 2


# Sayfa 2 içeriği
def page_2():
    st.title("Page 2: Image, Sliders, and Buttons")
    
    col1, col2, col3 = st.columns(3)
    
    # Yüklenen dosyanın resmini göster
    with col1:
        if st.session_state.uploaded_file is not None:
            st.image(st.session_state.uploaded_file, caption="Left Image", use_column_width=True)
        else:
            st.write("Lütfen bir resim yükleyin.")

    with col2:
        slider1 = st.slider("Slider 1", 0, 100, 50)
        slider2 = st.slider("Slider 2", 0, 100, 50)
        slider3 = st.slider("Slider 3", 0, 100, 50)
        button_cols = st.columns(4)
        
        with button_cols[0]:
            if st.button("Button 1"):
                st.write("Button 1 pressed")
        with button_cols[1]:
            if st.button("Button 2"):
                st.write("Button 2 pressed")
        with button_cols[2]:
            if st.button("Button 3"):
                st.write("Button 3 pressed")
        with button_cols[3]:
            if st.button("Button 4"):
                st.write("Button 4 pressed")

    # images_array kontrol et ve dolu olup olmadığını doğrula
    if "images_array" in st.session_state and st.session_state.images_array:
        st.session_state.images_array[0] = raw_output_image
        st.session_state.selected_image = raw_output_image
    
    with col3:
        st.image(raw_output_image, caption="Right Image", use_column_width=True)
    
    if st.button("İlerle", key="next_to_3"):
        st.session_state.page = 3

# Sayfa durumu kontrolü
if "page" not in st.session_state:
    st.session_state.page = 'login'

# Navigation fonksiyonunu sadece bir kez çalıştırmak için kontrol ediyoruz


if st.session_state.page == 'login':
    login()
elif st.session_state.page == 'register':
    register()
else:
    if not st.session_state['navigation_initialized']:
        navigation()  # Navigation'ı oluştur
        st.session_state['navigation_initialized'] = True  # Navigation'ın oluşturulduğunu işaretle


    # Mevcut sayfa durumuna göre sayfa içeriğini göster
    if st.session_state.page == 1:
        page_1()
    elif st.session_state.page == 2:
        page_2()
    elif st.session_state.page == 3:
        page_3()
    elif st.session_state.page == 4:
        page_4()

