# 🇹🇷 Türkiye Adres Verisi

> Türkiye'nin en güncel il, ilçe ve mahalle verilerini PTT'nin resmi kaynağından otomatik olarak toplayan açık kaynak proje.

## 📅 Son Güncelleme

**Son güncelleme:** 26 Kasım 2025, 01:43

## 🎯 Problem

Türkiye'de yazılım geliştiren her geliştiricinin karşılaştığı ortak bir sorun var: **güncel adres verisi bulmak**.

- 📅 Çoğu veri kaynağı güncel değil
- 🔄 Yeni ilçeler ve mahalleler ekleniyor, ancak veri setleri güncellenmiyor
- ⚠️ Eski verilerle çalışan uygulamalar hatalı sonuçlar üretiyor
- 💰 Ticari API'ler pahalı ve erişimi kısıtlı
- 📦 Açık kaynak alternatifler çoğunlukla eski ve bakımsız

Bu proje, bu sorunu çözmek için doğrudan **PTT'nin resmi web sitesinden** veri çekerek, Türkiye'deki tüm geliştiricilere ücretsiz ve güncel bir kaynak sunuyor.

## ✨ Özellikler

- 🔄 **Günlük Otomatik Güncelleme**: Veriler her gün otomatik olarak PTT'den çekilir
- 📍 **Resmi Kaynak**: Veriler PTT'nin resmi web sitesinden (`postakodu.ptt.gov.tr`) alınır
- 🆓 **Tamamen Ücretsiz**: Açık kaynak ve herkesin kullanımına açık
- 📊 **JSON Formatı**: Kolay entegrasyon için yapılandırılmış JSON formatında
- 🏙️ **Kapsamlı Veri**: İl, ilçe, mahalle ve posta kodu bilgileri
- 🤖 **Otomatik**: GitHub Actions ile tamamen otomatik çalışır

## 📚 Veri Yapısı

Proje, PTT'nin resmi web sitesinden (`https://postakodu.ptt.gov.tr`) aşağıdaki verileri çeker:

- **İller** (İl ID ve İl Adı)
- **İlçeler** (İlçe ID ve İlçe Adı)
- **Mahalleler** (Mahalle ID, Mahalle Adı ve Posta Kodu)

### Örnek Veri Yapısı

```json
[
  {
    "il_id": "34",
    "il_adi": "İstanbul",
    "ilceler": [
      {
        "ilce_id": "2054",
        "ilce_adi": "Kadıköy",
        "mahalleler": [
          {
            "mahalle_id": "12345",
            "mahalle_adi": "Acıbadem",
            "posta_kodu": "34718"
          }
        ]
      }
    ]
  }
]
```

## 🔄 Otomatik Güncelleme

Bu proje, **GitHub Actions** kullanarak her gün otomatik olarak çalışır ve verileri günceller. Yeni ilçeler, mahalleler veya posta kodları eklendiğinde, otomatik olarak veri setine dahil edilir.

## 🚀 Kullanım

### Veri Dosyalarına Erişim

Proje, çekilen verileri JSON formatında depolar. En güncel veri dosyasını repository'de bulabilirsiniz.

### Yerel Çalıştırma

Eğer script'i kendiniz çalıştırmak isterseniz:

```bash
# Bağımlılıkları yükleyin
pip install requests beautifulsoup4

# Script'i çalıştırın
python .github/scripts/scrape_ptt.py
```

## 🤝 Katkıda Bulunun

Bu proje, Türkiye'deki tüm geliştiriciler için bir kaynak. Katkılarınızı bekliyoruz!

### Nasıl Katkıda Bulunabilirsiniz?

- 🐛 **Hata Bildirimi**: Bir sorun bulduysanız issue açın
- 💡 **Öneriler**: Yeni fikirler ve önerilerinizi paylaşın
- 🔧 **Kod Katkısı**: Pull request göndererek projeyi geliştirin
- 📖 **Dokümantasyon**: Dokümantasyonu iyileştirmeye yardımcı olun
- ⭐ **Yıldız Verin**: Projeyi beğendiyseniz yıldız vermeyi unutmayın!

### Fikirler ve Öneriler

Aşağıdaki konularda fikirlerinizi paylaşabilirsiniz:

- Veri formatı iyileştirmeleri
- Yeni özellikler (örneğin: API endpoint, farklı formatlar)
- Performans optimizasyonları
- Dokümantasyon geliştirmeleri
- Test kapsamı artırımı

## 📝 Lisans

Bu proje açık kaynaklıdır ve topluluk tarafından geliştirilmektedir.

## 🙏 Teşekkürler

PTT'ye, resmi web sitesi üzerinden bu verileri sağladığı için teşekkür ederiz.

---

**Not**: Bu proje, PTT'nin resmi web sitesinden veri çekmektedir. Verilerin doğruluğu ve güncelliği PTT'nin kaynağına bağlıdır.
