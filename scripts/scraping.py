"""
Google Maps Yorumlar Scraping Script
Bu script bir mekanın Google Maps sayfasındaki yorumlar butonuna tıklar.
Terminal'den mekan adı alır ve otomatik olarak arar.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import sys
import csv
from datetime import datetime


def setup_driver():
    """Chrome driver'ı ayarla ve başlat"""
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--lang=tr")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # User agent ayarla
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # navigator.webdriver'ı gizle
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def search_place(driver, place_name: str):
    """Google Maps'te mekan ara"""
    # Doğrudan arama URL'si ile git
    search_url = f"https://www.google.com/maps/search/{place_name.replace(' ', '+')}"
    print(f"URL'ye gidiliyor: {search_url}")
    driver.get(search_url)
    
    # Sayfanın yüklenmesini bekle
    time.sleep(4)
    
    # Çerez kabul penceresini kapat (varsa)
    try:
        wait = WebDriverWait(driver, 3)
        # Türkçe ve İngilizce için farklı butonları dene
        for btn_text in ["Tümünü kabul et", "Kabul et", "Accept all", "Accept"]:
            try:
                accept_button = driver.find_element(By.XPATH, f"//button[contains(., '{btn_text}')]")
                accept_button.click()
                print("Çerez popup'ı kapatıldı.")
                time.sleep(1)
                break
            except:
                continue
    except:
        pass
    
    print(f"'{place_name}' için arama yapıldı.")
    time.sleep(2)


def click_first_result(driver):
    """İlk arama sonucuna tıkla (liste görünümünde ise)"""
    try:
        wait = WebDriverWait(driver, 5)
        # Sonuç listesindeki ilk öğeye tıkla
        first_result = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.Nv2PK a.hfpxzc")
        ))
        first_result.click()
        print("İlk sonuca tıklandı.")
        time.sleep(3)
        return True
    except:
        # Zaten detay sayfasındayız
        print("Zaten mekan detay sayfasında.")
        return True


def click_reviews_tab(driver):
    """
    Sol paneldeki Yorumlar tab'ına tıkla.
    button[role='tab'] ve class='hh2c6' olan elementin içinde 'Yorum' geçeni bulur.
    """
    from selenium.webdriver.common.action_chains import ActionChains
    
    wait = WebDriverWait(driver, 10)
    
    # Tüm tab butonlarını bul ve "Yorum" içereni seç
    selector = "//button[@role='tab' and contains(@class, 'hh2c6')]"
    
    try:
        print(f"Selector deneniyor: {selector}")
        
        # Tüm tab butonlarını bul
        elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, selector)))
        print(f"Bulunan tab sayısı: {len(elements)}")
        
        # Yorum içeren tab'ı bul
        target_element = None
        for el in elements:
            try:
                text = el.text or el.get_attribute("aria-label") or ""
                print(f"  Tab: '{text}'")
                if "Yorum" in text or "yorum" in text:
                    target_element = el
                    break
            except:
                continue
        
        if not target_element:
            # Eğer Yorum bulunamazsa 3. tab'ı dene (genelde Yorumlar oradadır)
            if len(elements) >= 3:
                target_element = elements[2]
                print("Yorum tab'ı bulunamadı, 3. tab seçildi.")
        
        if target_element:
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_element)
            time.sleep(0.5)
            
            # Yöntem 1: JavaScript click (en güvenilir)
            driver.execute_script("arguments[0].click();", target_element)
            print(f"✅ Yorumlar tab'ına JavaScript ile tıklandı!")
            time.sleep(2)
            return True
        else:
            print("❌ Hiçbir tab bulunamadı!")
            return False
        
    except Exception as e:
        print(f"❌ Yorumlar tab'ı bulunamadı: {e}")
        return False


def get_reviews(driver, scroll_count: int = 10):
    """
    Yorumları scroll ederek yükle ve topla.
    
    DOM Yapısı:
    div.m6QErb.XiKgde           (Ana scroll container - sol panel)
      └── div.jftiEf.fontBodyMedium   (Her bir yorum kartı)
            └── span.wiI7pd            (Yorum metni)
    """
    reviews = []
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # Yorumlar tab'ının yüklenmesini bekle
        time.sleep(2)
        
        # Sol paneldeki scroll container'ı bul
        # DİKKAT: Yorumlar tab'ı açıkken sol panel m6QErb.XiKgde class'ına sahip
        scrollable_div = None
        try:
            # Birden fazla m6QErb elementi olabilir, scrollable olanı bul
            elements = driver.find_elements(By.CSS_SELECTOR, "div.m6QErb")
            for el in elements:
                # Scroll yapılabilir mi kontrol et
                scroll_height = driver.execute_script("return arguments[0].scrollHeight", el)
                client_height = driver.execute_script("return arguments[0].clientHeight", el)
                if scroll_height > client_height:
                    scrollable_div = el
                    print(f"✅ Scrollable container bulundu (scrollHeight: {scroll_height})")
                    break
        except Exception as e:
            print(f"Container arama hatası: {e}")
        
        if not scrollable_div:
            print("❌ Scroll yapılabilir container bulunamadı!")
            return reviews
        
        # Scroll yaparak daha fazla yorum yükle
        print(f"\n📜 Yorumlar yükleniyor, {scroll_count} kez scroll yapılacak...")
        last_height = 0
        for i in range(scroll_count):
            # Scroll yap
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", 
                scrollable_div
            )
            
            # Yeni içeriğin yüklenmesini bekle
            time.sleep(2)
            
            # Yeni yükleme olup olmadığını kontrol et
            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            print(f"  Scroll {i+1}/{scroll_count} - Height: {new_height}")
            
            # Eğer height değişmediyse, tüm yorumlar yüklenmiş demektir
            if new_height == last_height:
                print("  ⚠️ Daha fazla yorum yok, scroll durduruluyor...")
                break
            last_height = new_height
        
        # Yorum kartlarını bul: div.jftiEf.fontBodyMedium
        review_cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf.fontBodyMedium")
        print(f"\n📝 Bulunan yorum kartı sayısı: {len(review_cards)}")
        
        # Her karttaki metni çek
        for idx, card in enumerate(review_cards):
            try:
                # Yorum metni: span.wiI7pd
                text_span = card.find_element(By.CSS_SELECTOR, "span.wiI7pd")
                review_text = text_span.text
                
                # Eğer metin boşsa atla
                if not review_text.strip():
                    continue
                
                # Rating (yıldız): span.kvMYJc
                try:
                    rating_el = card.find_element(By.CSS_SELECTOR, "span.kvMYJc")
                    rating = rating_el.get_attribute("aria-label")
                except:
                    rating = "N/A"
                
                # Kullanıcı adı: div.d4r55 veya button içindeki isim
                try:
                    user_el = card.find_element(By.CSS_SELECTOR, "div.d4r55")
                    username = user_el.text
                except:
                    try:
                        user_el = card.find_element(By.CSS_SELECTOR, "button.WEBjve")
                        username = user_el.get_attribute("aria-label")
                    except:
                        username = "Anonim"
                
                reviews.append({
                    "username": username,
                    "rating": rating,
                    "text": review_text
                })
                
            except Exception as e:
                continue
        
        print(f"\n✅ Toplam {len(reviews)} yorum toplandı!")
        return reviews
        
    except Exception as e:
        print(f"❌ Yorumlar yüklenirken hata: {e}")
        return reviews


def main():
    """Ana fonksiyon - terminal'den mekan adı alır"""
    
    # Terminal'den mekan adı al
    if len(sys.argv) > 1:
        place_name = " ".join(sys.argv[1:])
    else:
        place_name = input("Mekan adını girin: ").strip()
    
    if not place_name:
        print("Mekan adı boş olamaz!")
        return
    
    print(f"\n🔍 Aranan mekan: {place_name}")
    print("=" * 50)
    
    print("Chrome driver başlatılıyor...")
    driver = setup_driver()
    
    try:
        # Mekanı ara
        search_place(driver, place_name)
        
        # İlk sonuca tıkla (gerekirse)
        click_first_result(driver)
        time.sleep(5)
        # Yorumlar tab'ına tıkla
        success = click_reviews_tab(driver)
        
        if success:
            print("\n" + "=" * 50)
            print("✅ Yorumlar sayfası açıldı!")
            print("=" * 50)
            
            # Yorumları topla (max 10 scroll, daha az yorum varsa erken durur)
            reviews = get_reviews(driver, scroll_count=10)
            
            # Her yoruma ID ekle
            for i, r in enumerate(reviews, 1):
                r['id'] = i
            
            # Yorumları CSV'ye kaydet
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_place_name = place_name.replace(' ', '_').replace('/', '_')[:30]
            csv_filename = f"reviews_{safe_place_name}_{timestamp}.csv"
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'username', 'rating', 'text']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for r in reviews:
                    writer.writerow({
                        'id': r['id'],
                        'username': r['username'],
                        'rating': r['rating'],
                        'text': r['text']
                    })
            
            print(f"\n💾 Yorumlar '{csv_filename}' dosyasına kaydedildi!")
            print(f"   Toplam {len(reviews)} yorum kaydedildi.")
            
            # Yorumları ekrana yazdır (özet)
            print("\n" + "=" * 50)
            print("📋 YORUMLAR (ilk 5):")
            print("=" * 50)
            for r in reviews[:5]:
                print(f"\n--- Yorum {r['id']} ---")
                print(f"👤 {r['username']}")
                print(f"⭐ {r['rating']}")
                print(f"💬 {r['text'][:150]}{'...' if len(r['text']) > 150 else ''}")
            
            if len(reviews) > 5:
                print(f"\n... ve {len(reviews) - 5} yorum daha (CSV dosyasına bakın)")
            
            # Kullanıcı input bekle
            input("\nTarayıcıyı kapatmak için ENTER'a basın...")
        else:
            print("\n❌ Yorumlar tab'ına tıklanamadı!")
            input("\nTarayıcıyı kapatmak için ENTER'a basın...")
            
    except Exception as e:
        print(f"Hata oluştu: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("Tarayıcı kapatıldı.")


if __name__ == "__main__":
    main()
