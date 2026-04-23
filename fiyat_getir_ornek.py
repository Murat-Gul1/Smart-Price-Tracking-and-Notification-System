"""
fiyat_getir(url) — Asenkron Fiyat Çekme Fonksiyonu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Playwright + playwright-stealth kullanarak herhangi bir
e-ticaret sitesinden ürün fiyatı ve görsel URL'si çeker.

Kullanım:
    import asyncio
    from fiyat_getir_ornek import fiyat_getir

    sonuc = asyncio.run(fiyat_getir("https://www.ornek-site.com/urun/123"))
    print(sonuc)

NOT: CSS seçicileri örnek olarak bırakılmıştır.
     Hedef siteye göre güncellemeniz gerekir.
"""

import asyncio
import random
from typing import Dict, Any

from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth


# ═══════════════════════════════════════════════════════════
#  USER-AGENT HAVUZU
#  Her çalıştırmada buradan rastgele biri seçilir.
#  Gerçek Chrome/Firefox/Edge sürümleriyle güncel tutun.
# ═══════════════════════════════════════════════════════════
USER_AGENTS = [
    # Windows 10/11 — Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    # Windows — Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    # macOS — Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # macOS — Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    # Windows — Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    # Linux — Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

# ═══════════════════════════════════════════════════════════
#  VIEWPORT (EKRAN) BOYUTLARI HAVUZU
#  Gerçek masaüstü çözünürlükleri — her çalıştırmada
#  rastgele biri seçilir; bot profilinden kaçınır.
# ═══════════════════════════════════════════════════════════
VIEWPORT_BOYUTLARI = [
    {"width": 1920, "height": 1080},   # Full HD (en yaygın)
    {"width": 1920, "height": 1200},   # Full HD geniş
    {"width": 2560, "height": 1440},   # 2K / QHD
    {"width": 1680, "height": 1050},   # WSXGA+
    {"width": 1440, "height": 900},    # MacBook Air 13"
    {"width": 1536, "height": 864},    # HD+ (yaygın dizüstü)
    {"width": 1280, "height": 800},    # WXGA
    {"width": 1366, "height": 768},    # HD (en yaygın dizüstü)
    {"width": 1600, "height": 900},    # HD+
    {"width": 1280, "height": 1024},   # SXGA
]


# ═══════════════════════════════════════════════════════════
#  CSS SEÇİCİLERİ (Hedef siteye göre güncelleyin)
# ═══════════════════════════════════════════════════════════
# Her seçici bir liste olarak tanımlanmıştır.
# Fonksiyon bu listeyi sırayla dener, ilk eşleşeni kullanır.
# Böylece birden fazla site/layout için esneklik sağlanır.

FIYAT_SECICILERI = [
    # Trendyol (Öncelikli)
    "span.prc-dsc",
    "span.prc-slg",
    # Amazon
    "span.a-price span.a-offscreen",
    "span.a-price-whole",
    # Hepsiburada
    "span[data-bind='markupText: currentPriceBeforePoint']",
    # Genel e-ticaret siteleri için yaygın seçiciler
    ".product-price",
    ".price",
    "[class*='price']",
    "[data-testid='price']",
]

GORSEL_SECICILERI = [
    # Trendyol (Öncelikli)
    ".gallery-container img",
    "img.detail-section-img",
    # Amazon
    "#landingImage",
    "#imgBlkFront",
    # Hepsiburada
    "img.product-image",
    # Genel
    ".gallery img",
    "img[alt*='ürün']",
    "img.product-image",
    "[data-testid='product-image'] img",
]


# ═══════════════════════════════════════════════════════════
#  ANA FONKSİYON
# ═══════════════════════════════════════════════════════════

async def fiyat_getir(url: str) -> Dict[str, Any]:
    """
    Verilen URL'den ürün fiyatını ve görsel URL'sini asenkron olarak çeker.

    Playwright ile headless Chromium tarayıcı başlatır,
    playwright-stealth eklentisini uygulayarak bot tespitini engeller,
    sayfanın yüklenmesi için rastgele 2–5 saniye bekler ve
    CSS seçicileri ile fiyat/görsel bilgisini toplar.

    Args:
        url: Ürün sayfasının tam URL'si.

    Returns:
        dict: Aşağıdaki anahtarları içerir:
            - fiyat      (str): Ürün fiyatı veya "Fiyat bulunamadı"
            - gorsel_url (str): Ürün görseli URL'si veya "Görsel bulunamadı"
            - hata       (str | None): Varsa hata mesajı, yoksa None
    """

    # Varsayılan sonuç sözlüğü
    sonuc: Dict[str, Any] = {
        "fiyat": "Fiyat bulunamadı",
        "gorsel_url": "Görsel bulunamadı",
        "hata": None,
    }

    browser = None

    try:
        async with async_playwright() as p:

            # ── 1. Headless Chromium tarayıcıyı başlat ────────────

            # Her çalıştırmada farklı UA ve viewport seç
            secilen_ua       = random.choice(USER_AGENTS)
            secilen_viewport = random.choice(VIEWPORT_BOYUTLARI)
            w, h = secilen_viewport["width"], secilen_viewport["height"]

            print(f"🕵️  Seçilen User-Agent : {secilen_ua[:60]}...")
            print(f"🖥️  Seçilen Viewport   : {w}x{h}")

            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    f"--window-size={w},{h}",  # viewport ile uyumlu pencere
                    "--disable-extensions",
                    "--disable-plugins-discovery",
                    "--disable-notifications",
                ],
            )

            # Gerçekçi tarayıcı profili
            context = await browser.new_context(
                viewport=secilen_viewport,
                screen={"width": w, "height": h},   # fiziksel ekran = viewport
                user_agent=secilen_ua,
                locale="tr-TR",
                timezone_id="Europe/Istanbul",
                color_scheme="light",
                java_script_enabled=True,
                accept_downloads=False,
                extra_http_headers={
                    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                },
            )

            page = await context.new_page()

            # ── 2. playwright-stealth eklentisini entegre et ──────
            stealth = Stealth()
            await stealth.apply_stealth_async(page)

            # ── 3. Ek JavaScript anti-detection önlemleri ──────────
            # Bu script sayfa yüklenmeden önce enjekte edilir.
            await page.add_init_script("""
                // WebDriver özelliğini gizle (en temel bot tespiti)
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Gerçek Chrome nesnesi simüle et
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };

                // Permissions API'yi override et (headless tespitini engeller)
                const _origQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (params) =>
                    params.name === 'notifications'
                        ? Promise.resolve({ state: Notification.permission })
                        : _origQuery(params);

                // Gerçekçi plugin listesi ekle
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // Gerçekçi dil listesi
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['tr-TR', 'tr', 'en-US', 'en']
                });

                // Donanım eşzamanlılığı (CPU çekirdek sayısı)
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8
                });

                // Cihaz belleği (GB)
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8
                });
            """);

            print(f"🌐 Siteye gidiliyor: {url}")

            # Sayfaya git (DOM içeriği yüklenene kadar bekle)
            await page.goto(url, wait_until="domcontentloaded", timeout=45_000)

            # ── 3. Rastgele 2–5 saniye bekle (insan simülasyonu) ──
            bekleme_suresi = random.uniform(2.0, 5.0)
            print(f"⏳ Sayfa yüklendi, {bekleme_suresi:.2f} saniye bekleniyor...")
            await asyncio.sleep(bekleme_suresi)

            # ── 4. Fiyatı bul ─────────────────────────────────────
            try:
                for secici in FIYAT_SECICILERI:
                    fiyat_elementi = await page.query_selector(secici)
                    if fiyat_elementi:
                        fiyat_metni = await fiyat_elementi.inner_text()
                        if fiyat_metni and fiyat_metni.strip():
                            sonuc["fiyat"] = fiyat_metni.strip()
                            print(f"✅ Fiyat bulundu: {sonuc['fiyat']}")
                            break
                else:
                    # Hiçbir seçici eşleşmedi — wait_for_selector ile son deneme
                    try:
                        genel_secici = ", ".join(FIYAT_SECICILERI[:4])
                        fiyat_el = await page.wait_for_selector(
                            genel_secici, timeout=5_000
                        )
                        if fiyat_el:
                            metin = await fiyat_el.inner_text()
                            if metin and metin.strip():
                                sonuc["fiyat"] = metin.strip()
                                print(f"✅ Fiyat bulundu (bekleme sonrası): {sonuc['fiyat']}")
                    except Exception:
                        pass  # Zaman aşımı — varsayılan mesaj kalır

                if sonuc["fiyat"] == "Fiyat bulunamadı":
                    print("⚠️  Fiyat alınamadı: Hiçbir CSS seçici eşleşmedi.")

            except Exception as fiyat_hatasi:
                print(f"⚠️  Fiyat alınırken hata oluştu: {fiyat_hatasi}")

            # ── 5. Ürün görselinin URL'sini bul ───────────────────
            try:
                for secici in GORSEL_SECICILERI:
                    gorsel_elementi = await page.query_selector(secici)
                    if gorsel_elementi:
                        # Önce 'src', sonra 'data-src' (lazy-load) dene
                        gorsel_src = (
                            await gorsel_elementi.get_attribute("src")
                            or await gorsel_elementi.get_attribute("data-src")
                        )
                        if gorsel_src and gorsel_src.startswith("http"):
                            sonuc["gorsel_url"] = gorsel_src
                            print(f"✅ Görsel URL bulundu: {sonuc['gorsel_url'][:80]}...")
                            break

                if sonuc["gorsel_url"] == "Görsel bulunamadı":
                    # Fallback: og:image meta tag'inden dene
                    try:
                        og_image = await page.evaluate(
                            "() => document.querySelector('meta[property=\"og:image\"]')?.content || ''"
                        )
                        if og_image:
                            sonuc["gorsel_url"] = og_image
                            print(f"✅ Görsel URL (og:image) bulundu: {og_image[:80]}...")
                    except Exception:
                        pass

                if sonuc["gorsel_url"] == "Görsel bulunamadı":
                    print("⚠️  Görsel alınamadı: Hiçbir CSS seçici eşleşmedi.")

            except Exception as gorsel_hatasi:
                print(f"⚠️  Görsel alınırken hata oluştu: {gorsel_hatasi}")

            # Tarayıcıyı kapat
            await browser.close()
            browser = None  # finally bloğunda tekrar kapatmayı önle

    except Exception as genel_hata:
        hata_mesaji = f"Genel hata oluştu: {genel_hata}"
        print(f"❌ {hata_mesaji}")
        sonuc["hata"] = hata_mesaji

    finally:
        # Tarayıcı herhangi bir sebeple hâlâ açıksa kapat
        if browser:
            try:
                await browser.close()
            except Exception:
                pass

    return sonuc


# ═══════════════════════════════════════════════════════════
#  ÖRNEK KULLANIM TESTİ
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":

    async def test():
        test_url = "https://www.trendyol.com/apple/iphone-15-128-gb-p-782425137"
        print("=" * 60)
        print("🛒  fiyat_getir() Test Başlatılıyor...")
        print("=" * 60)

        data = await fiyat_getir(test_url)

        print("\n" + "─" * 40)
        print("📦 SONUÇ:")
        print("─" * 40)
        print(f"  💰 Fiyat      : {data['fiyat']}")
        print(f"  🖼️  Görsel URL : {data['gorsel_url']}")
        if data["hata"]:
            print(f"  ❌ Hata       : {data['hata']}")
        print("─" * 40)

    asyncio.run(test())
