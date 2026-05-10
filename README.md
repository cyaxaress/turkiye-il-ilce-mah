# Türkiye il, ilçe ve mahalle verisi

Türkiye genelinde **il**, **ilçe** ve **mahalle** (posta kodu dahiye) hiyerarşisini [PTT](https://www.ptt.gov.tr) kaynağından düzenli olarak çeken ve JSON olarak yayımlayan açık kaynak bir veri deposudur. Amaç, uygulamalarda güncel ve tutarlı adres seçimleri için tek bir güvenilir kaynak sunmaktır.

## 📅 Son Güncelleme

**Son güncelleme:** 10 Mayıs 2026, 02:47

## Veri özeti

Son tam çekimdeki kayıt sayıları:

<!-- PTT_STATS_TABLE_START -->
| İl | İlçe | Mahalle |
| ---: | ---: | ---: |
| 81 | 973 | 72985 |
<!-- PTT_STATS_TABLE_END -->

## İçindekiler

- [Veri özeti](#veri-özeti)
- [Neden bu depo?](#neden-bu-depo)
- [Özellikler](#özellikler)
- [Veri şeması](#veri-şeması)
- [Depo düzeni](#depo-düzeni)
- [Slug ve dosya yolları](#slug-ve-dosya-yolları)
- [Yerel çalıştırma](#yerel-çalıştırma)
- [Katkı](#katkı)
- [Sorumluluk reddi](#sorumluluk-reddi)

## Neden bu depo?

Türkiye adres verisiyle çalışan projelerde sık karşılaşılan sorunlar:

- Kamuya açık veya üçüncü parti listelerin güncelliğinin düşmesi
- İdari değişikliklerin (yeni ilçe, mahalle, posta kodu) yansımaması
- Ticari API maliyeti veya kullanım kısıtları

Bu depo, veriyi doğrudan PTT üzerinden alır; günlük zamanlanmış iş akışı ile dosyalar güncellenir.

## Özellikler

|               |                                                 |
| ------------- | ----------------------------------------------- |
| **Güncellik** | Günlük otomatik çekim                           |
| **Kaynak**    | `https://www.ptt.gov.tr`                        |
| **Kapsam**    | İl → ilçe → mahalle; mahalle bazında posta kodu |

## Veri şeması

Her il kaydı şu alanları içerir (mahalle listesi ilçe altında):

| Alan                               | Açıklama                                                                                 |
| ---------------------------------- | ---------------------------------------------------------------------------------------- |
| `il_id`                            | PTT il tanımlayıcısı                                                                     |
| `il_adi`                           | İl adı                                                                                   |
| `il_slug`                          | Klasör adlarıyla eşleşen URL-dostu tanımlayıcı (birleşik dosyada ve `iller.json` içinde) |
| `ilceler`                          | İlçe dizisi                                                                              |
| `ilce_id`, `ilce_adi`, `ilce_slug` | İlçe tanımı ve slug                                                                      |
| `mahalleler`                       | `mahalle_id`, `mahalle_adi`, `posta_kodu` alanları                                       |

Örnek (özet):

```json
[
  {
    "il_id": "34",
    "il_adi": "İstanbul",
    "il_slug": "istanbul",
    "ilceler": [
      {
        "ilce_id": "2054",
        "ilce_adi": "Kadıköy",
        "ilce_slug": "kadikoy",
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

## Depo düzeni

### Birleşik dosya

| Yol                                                            | İçerik                                                      |
| -------------------------------------------------------------- | ----------------------------------------------------------- |
| [`PTT/ptt_il_ilce_mahalle.json`](PTT/ptt_il_ilce_mahalle.json) | Tüm ülke; tek istekte veya tam ağaç ihtiyacı için uygundur. |

### `PTT/iller` — il ve ilçe bazında bölünmüş dosyalar

Aynı bilgi, küçük parçalar halinde okunabilir:

```text
PTT/
├── ptt_il_ilce_mahalle.json
└── iller/
    ├── iller.json
    ├── istanbul/
    │   ├── ilceler.json
    │   ├── uskudar/
    │   │   └── mahalleler.json
    │   └── kadikoy/
    │       └── mahalleler.json
    └── ankara/
        ├── ilceler.json
        └── ...
```

| Yol                                | Dosya                                | İçerik                                  |
| ---------------------------------- | ------------------------------------ | --------------------------------------- |
| `PTT/iller/`                       | [`iller.json`](PTT/iller/iller.json) | Tüm iller; `il_id`, `il_adi`, `il_slug` |
| `PTT/iller/{il_slug}/`             | `ilceler.json`                       | O ile ait ilçeler; `ilce_slug` dahil    |
| `PTT/iller/{il_slug}/{ilce_slug}/` | `mahalleler.json`                    | Mahalleler ve posta kodları             |

Örnek doğrudan kullanım: [İstanbul / Üsküdar mahalleleri](PTT/iller/istanbul/uskudar/mahalleler.json).

```mermaid
flowchart LR
    M["ptt_il_ilce_mahalle.json"]
    G["generate_iller_structure.py"]
    T["PTT/iller/ ..."]
    M --> G --> T
```

## Slug ve dosya yolları

- `PTT/iller/` altındaki **il klasör adı**, `iller.json` ve birleşik JSON’daki **`il_slug`** ile aynıdır (ör. `istanbul`, `sanliurfa`).
- İl altındaki **ilçe klasör adı**, ilgili **`ilce_slug`** ile aynıdır (ör. `uskudar`, `merkez`).
- Slug’lar dosya sistemi ve URL’ler için ASCII’ye indirgenmiş adlardan türetilir; haritalama için her zaman [`PTT/iller/iller.json`](PTT/iller/iller.json) ve ilgili `ilceler.json` dosyalarına başvurun.

## Yerel çalıştırma

**Gereksinimler:** Python 3.11+ önerilir (iş akışlarıyla uyumlu). Scraper doğrudan `requests` kullanır; `urllib3` uyarılarını bastırmak için betiğe dahildir.

```bash
pip install requests
python .github/scripts/scrape_ptt.py
```

Birleşik dosyayı elle veya farklı bir kaynaktan güncelledikten sonra klasör ağacını yeniden oluşturmak için:

```bash
python .github/scripts/generate_iller_structure.py
```

## Katkı

- Hata veya tutarsızlık: [Issues](https://github.com/cyaxaress/tukiye-address/issues) üzerinden bildirin.
- İyileştirme veya yeni format: önce kısa bir tartışma veya PR açıklamasıyla hedefi netleştirin.
- Bu README’deki **Son güncelleme** ve **Veri özeti** tablosu (`<!-- PTT_STATS_TABLE_START -->` … `<!-- PTT_STATS_TABLE_END -->` aralığı) otomatik güncellenir; bu başlık veya işaretçi metinleri değiştirilirse scraper’daki düzenli ifadeler de güncellenmelidir.

## Sorumluluk reddi

Veri, PTT’nin yayınladığı kaynağa dayanır; doğruluk ve güncellik nihai olarak o kaynağa bağlıdır. Bu depo resmi bir PTT ürünü değildir; üretim ortamında kritik kararlar için kaynakla çapraz kontrol önerilir.

Teşekkür: Adres bilgisini kamuya açık arayüz ve API ile sunan PTT’ye.

---

_Lisans: Depoda ayrı bir `LICENSE` dosyası yoksa, kullanım koşulları depo sahibinin tercihine göre netleştirilmelidir._
