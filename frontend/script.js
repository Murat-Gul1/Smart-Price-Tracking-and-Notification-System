document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('tracker-form');
    const contactRadios = document.querySelectorAll('input[name="contact-method"]');
    const contactLabel = document.getElementById('contact-label');
    const contactIcon = document.getElementById('contact-icon');
    const contactInput = document.getElementById('contact-info');
    const productUrlInput = document.getElementById('product-url');
    const imageBox = document.getElementById('product-image-box');
    const statusMessage = document.getElementById('status-message');

    // İletişim tercihi değiştiğinde label ve ikonu güncelleme
    contactRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'telegram') {
                contactLabel.textContent = 'Telegram Username or Number';
                contactIcon.className = 'fa-solid fa-address-book';
                contactInput.placeholder = 'e.g. @username';
            } else {
                contactLabel.textContent = 'Email Address';
                contactIcon.className = 'fa-solid fa-at';
                contactInput.placeholder = 'e.g. email@address.com';
            }
        });
    });

    // Form gönderilme olayı
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Form verilerini al
        const url = productUrlInput.value;
        const targetPrice = document.getElementById('target-price').value;
        const contactMethod = document.querySelector('input[name="contact-method"]:checked').value;
        const contactInfo = contactInput.value;
        const notificationType = document.querySelector('input[name="notification-type"]:checked')?.value || 'mandatory';

        // Gerçek bir backend'e bağlandığında bu kısımdan veriler gönderilecek.
        console.log('Tracking Request Started:', { url, targetPrice, contactMethod, contactInfo, notificationType });

        // Simülasyon: Kullanıcıya bilgi ver ve görseli yükleme simülasyonunu başlat
        statusMessage.innerHTML = '<span style="color: #4ade80;"><i class="fa-solid fa-circle-check"></i> Tracking successfully started!</span>';
        
        // Butonu geçici olarak devre dışı bırak, loading ver
        const btn = form.querySelector('.submit-btn');
        const originalBtnHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        btn.disabled = true;

        setTimeout(() => {
            btn.innerHTML = originalBtnHTML;
            btn.disabled = false;
            // Bot çalıştığında çekilen görselin buraya getirilmesi için fonksiyonu tetikle (Simülasyon)
            simulateBotFetchingImage(url);
        }, 1500);
    });

    // URL değiştiğinde tetiklenecek görsel çekme simülasyonu
    productUrlInput.addEventListener('input', debounce((e) => {
        const url = e.target.value;
        if (url && isValidURL(url)) {
            simulateBotFetchingImage(url);
        } else {
            resetImageBox();
            if(!url) {
                statusMessage.textContent = 'Please enter a product link.';
            } else {
                statusMessage.textContent = 'Waiting for a valid URL...';
            }
        }
    }, 1000));
});

// Bot görseli çektiğinde çağrılacak asıl fonksiyon (şimdilik dışa açık / hazır tutuluyor)
function updateProductImage(imageUrl) {
    const imageBox = document.getElementById('product-image-box');
    const placeholder = document.getElementById('image-placeholder');
    const imgElement = document.getElementById('product-image');
    const scanningAnimation = document.getElementById('scanning-animation');
    const statusMessage = document.getElementById('status-message');

    // Animasyonu durdur
    if(scanningAnimation) scanningAnimation.style.display = 'none';

    if (imageUrl) {
        // Görsel varsa göster
        placeholder.style.display = 'none';
        imgElement.src = imageUrl;
        imgElement.style.display = 'block';
        
        // Yüklenmesini bekle ve görünür yap
        imgElement.onload = () => {
            imgElement.style.opacity = '1';
            imageBox.classList.add('has-image');
            statusMessage.innerHTML = '<span style="color: #60a5fa;"><i class="fa-solid fa-circle-info"></i> Product detected.</span>';
        };

        imgElement.onerror = () => {
            resetImageBox('Image could not be loaded. Check the link.');
        };
    } else {
        resetImageBox();
    }
}

// ------ YARDIMCI FONKSİYONLAR VE SİMÜLASYONLAR ------

function simulateBotFetchingImage(url) {
    const placeholder = document.getElementById('image-placeholder');
    const scanningAnimation = document.getElementById('scanning-animation');
    const statusMessage = document.getElementById('status-message');
    const imgElement = document.getElementById('product-image');

    // Görsel zaten varsa sıfırla
    imgElement.style.opacity = '0';
    setTimeout(() => { imgElement.style.display = 'none'; }, 500);

    // Animasyonları başlat
    placeholder.style.display = 'flex';
    placeholder.querySelector('span').textContent = 'Scanning website...';
    placeholder.querySelector('i').className = 'fa-solid fa-radar fa-spin';
    scanningAnimation.style.display = 'block';
    
    statusMessage.textContent = 'The bot is currently visiting the site and looking for the image...';

    // X saniye sonra sahte bir görsel bulmuş gibi davran
    // Gerçek sistemde bot backend'den görsel url'ini websocket/api ile buraya yollayacak.
    setTimeout(() => {
        // Örnek bir placeholder product image
        const dummyImageUrl = 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80';
        updateProductImage(dummyImageUrl);
    }, 2500);
}

function resetImageBox(msg = 'Please enter a product link.') {
    const imageBox = document.getElementById('product-image-box');
    const placeholder = document.getElementById('image-placeholder');
    const imgElement = document.getElementById('product-image');
    const scanningAnimation = document.getElementById('scanning-animation');
    const statusMessage = document.getElementById('status-message');

    imageBox.classList.remove('has-image');
    imgElement.style.opacity = '0';
    setTimeout(() => { imgElement.style.display = 'none'; }, 500);
    
    placeholder.style.display = 'flex';
    placeholder.querySelector('span').textContent = 'Waiting for Product Image...';
    placeholder.querySelector('i').className = 'fa-solid fa-image';
    if(scanningAnimation) scanningAnimation.style.display = 'none';
    
    statusMessage.textContent = msg;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function isValidURL(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;  
    }
}
