#!/usr/bin/env python3
"""
Kanal linki test dosyası
Farklı kanal link formatlarını test eder
"""

from telegram_bot import TelegramBot

def test_channel_links():
    """Kanal linklerini test eder"""
    print("=" * 60)
    print("🔗 Kanal Linki Testi")
    print("=" * 60)
    
    # Test linkleri
    test_links = [
        # Normal kanallar
        "https://t.me/kanal_adi",
        "@kanal_adi", 
        "t.me/kanal_adi",
        "kanal_adi",
        
        # Gizli kanallar
        "https://t.me/+uro2qpwhl5ZiNDhk",
        "t.me/+uro2qpwhl5ZiNDhk",
        "+uro2qpwhl5ZiNDhk",
        
        # Geçersiz linkler
        "https://example.com",
        "invalid_link",
        "t.me/",
        "@",
        "+",
        ""
    ]
    
    # Bot instance oluştur (sadece test için)
    bot = TelegramBot()
    
    print("Test edilen linkler:\n")
    
    for i, link in enumerate(test_links, 1):
        is_valid = bot.is_valid_channel_link(link)
        status = "✅ GEÇERLİ" if is_valid else "❌ GEÇERSİZ"
        
        print(f"{i:2}. {link:40} -> {status}")
    
    print("\n" + "=" * 60)
    print("📊 Test Sonuçları")
    print("=" * 60)
    
    # Geçerli linkleri say
    valid_links = [link for link in test_links if bot.is_valid_channel_link(link)]
    invalid_links = [link for link in test_links if not bot.is_valid_channel_link(link)]
    
    print(f"✅ Geçerli linkler: {len(valid_links)}")
    print(f"❌ Geçersiz linkler: {len(invalid_links)}")
    
    print(f"\nGeçerli linkler:")
    for link in valid_links:
        print(f"  • {link}")
    
    print(f"\nGeçersiz linkler:")
    for link in invalid_links:
        print(f"  • {link}")
    
    # Özel test: Gizli kanal linki
    print(f"\n🔍 Özel Test:")
    special_link = "https://t.me/+uro2qpwhl5ZiNDhk"
    is_special_valid = bot.is_valid_channel_link(special_link)
    print(f"Gizli kanal linki '{special_link}' -> {'✅ GEÇERLİ' if is_special_valid else '❌ GEÇERSİZ'}")

if __name__ == "__main__":
    test_channel_links()
