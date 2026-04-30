#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import html
import json
import os
import random
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PTTAddressApiScraper:
    """PTT /api/posta-kodu üzerinden il / ilçe / mahalle + posta kodu çeker."""

    BASE_URL = "https://www.ptt.gov.tr"
    API_PATH = "/api/posta-kodu"

    TURKISH_LOWERCASE = {
        "İ": "i",
        "I": "ı",
        "Ğ": "ğ",
        "Ş": "ş",
        "Ç": "ç",
        "Ö": "ö",
        "Ü": "ü",
    }

    # ASCII slug (Türkçe karakterler latin harfine)
    _SLUG_TRANSLIT = str.maketrans(
        {
            "ı": "i",
            "İ": "i",
            "I": "i",
            "ğ": "g",
            "Ğ": "g",
            "ü": "u",
            "Ü": "u",
            "ş": "s",
            "Ş": "s",
            "ö": "o",
            "Ö": "o",
            "ç": "c",
            "Ç": "c",
        }
    )

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Expect": "",
                "Connection": "keep-alive",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            }
        )
        self.total_states = 0
        self.total_provinces = 0
        self.total_neighborhoods = 0

    def capitalize_first_letter(self, text: str) -> str:
        words = re.split(r"\s+", text.strip()) or []
        out: List[str] = []
        for word in words:
            if not word:
                continue
            first = word[0]
            rest = word[1:]
            rest_lower = ""
            for ch in rest:
                rest_lower += self.TURKISH_LOWERCASE.get(ch, ch.lower())
            out.append(first + rest_lower)
        return " ".join(out)

    def clean_text(self, text: str) -> str:
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text.strip())
        return self.capitalize_first_letter(text)

    def slugify(self, name: str, fallback: str = "x") -> str:
        """İl / ilçe / mahalle adından URL-dostu ASCII slug üretir."""
        s = name.translate(self._SLUG_TRANSLIT).lower()
        s = re.sub(r"[^a-z0-9]+", "-", s)
        s = re.sub(r"-{2,}", "-", s).strip("-")
        return s if s else fallback

    def _call_api(self, action: str, **params: str) -> List[Dict[str, Any]]:
        """cURL/SSL kopmalarına karşı HTTP/1.1 + üstel geri deneme (PHP ile aynı mantık)."""
        max_attempts = 6
        url = f"{self.BASE_URL}{self.API_PATH}"
        body: Dict[str, Any] = {"action": action, **params}
        last_exc: Optional[Exception] = None

        for attempt in range(1, max_attempts + 1):
            try:
                r = self.session.post(
                    url,
                    json=body,
                    timeout=(15, 60),
                    verify=False,
                )
                r.raise_for_status()
                payload = r.json()
                if isinstance(payload, dict) and "error" in payload:
                    msg = str(payload["error"])
                    raise RuntimeError(f"PTT API hatası ({action}): {msg}")
                if not isinstance(payload, list):
                    raise RuntimeError(f"Beklenmeyen API cevabı: {action}")
                return payload
            except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
                last_exc = e
                if attempt >= max_attempts:
                    break
                delay_ms = min(
                    30_000,
                    int(500 * (2 ** (attempt - 1))) + random.randint(0, 500),
                )
                if self.verbose:
                    print(
                        f"PTT API bağlantı hatası ({action}), {delay_ms} ms sonra "
                        f"tekrar deneniyor ({attempt}/{max_attempts}): {e}"
                    )
                time.sleep(delay_ms / 1000.0)

        raise last_exc or RuntimeError(f"PTT API çağrısı başarısız: {action}")

    def fetch_iller(self) -> List[Dict[str, Any]]:
        data = self._call_api("iller")
        return [il for il in data if int(il.get("kod") or 0) > 0]

    def fetch_ilceler(self, il_kodu: str) -> List[Dict[str, Any]]:
        data = self._call_api("ilceler", il_kodu=il_kodu)
        return [x for x in data if int(x.get("kod") or 0) > 0]

    def fetch_posta_kodlari(self, il_kodu: str, ilce_kodu: str) -> List[Dict[str, Any]]:
        data = self._call_api("postakodu", il_kodu=il_kodu, ilce_kodu=ilce_kodu)
        return [row for row in data if "mahalleAdi" in row]

    def scrape(self) -> List[Dict[str, Any]]:
        print("PTT Adres Verisi (v2, API) Çekme İşlemi Başlatılıyor")

        iller = self.fetch_iller()
        self.total_states = len(iller)
        address_data: List[Dict[str, Any]] = []

        for state_index, il in enumerate(iller, 1):
            il_kodu = str(il["kod"])
            il_adi = self.clean_text(str(il.get("ad", "")))

            current_province: Dict[str, Any] = {
                "il_id": il_kodu,
                "il_adi": il_adi,
                "il_slug": self.slugify(il_adi, fallback=f"il-{il_kodu}"),
                "ilceler": [],
            }

            ilceler = self.fetch_ilceler(il_kodu)
            for ilce in ilceler:
                ilce_kodu = str(ilce["kod"])
                ilce_adi = self.clean_text(str(ilce.get("ad", "")))
                province_source_id = f"{il_kodu}_{ilce_kodu}"
                self.total_provinces += 1

                posta_kodlari = self.fetch_posta_kodlari(il_kodu, ilce_kodu)
                seen: Dict[str, bool] = {}
                mahalleler: List[Dict[str, Optional[str]]] = []

                for row in posta_kodlari:
                    mahalle_adi_raw = row.get("mahalleAdi") or ""
                    mahalle_adi = self.clean_text(str(mahalle_adi_raw))
                    if not mahalle_adi:
                        continue

                    pk = row.get("posta_Kodu") or row.get("posta_kodu") or ""
                    posta_kodu = str(pk).strip() if pk is not None else ""
                    unique_key = (mahalle_adi.upper() + "|" + posta_kodu)
                    if unique_key in seen:
                        continue
                    seen[unique_key] = True

                    digest = hashlib.md5(unique_key.encode("utf-8")).hexdigest()
                    mahalle_id = f"{province_source_id}_{digest}"

                    mahalleler.append(
                        {
                            "mahalle_id": mahalle_id,
                            "mahalle_adi": mahalle_adi,
                            "mahalle_slug": self.slugify(
                                mahalle_adi, fallback=f"mahalle-{digest[:8]}"
                            ),
                            "posta_kodu": posta_kodu if posta_kodu else None,
                        }
                    )
                    self.total_neighborhoods += 1

                current_province["ilceler"].append(
                    {
                        "ilce_id": ilce_kodu,
                        "ilce_adi": ilce_adi,
                        "ilce_slug": self.slugify(
                            ilce_adi, fallback=f"ilce-{il_kodu}-{ilce_kodu}"
                        ),
                        "mahalleler": mahalleler,
                    }
                )

            address_data.append(current_province)

            print(f"[{state_index}/{self.total_states}] {il_adi} tamamlandı.")
            time.sleep(0.12)

        print()
        print(
            f"Tamamlandı: {self.total_states} il, "
            f"{self.total_provinces} ilçe, {self.total_neighborhoods} mahalle işlendi."
        )
        self._print_summary_table(
            self.total_states, self.total_provinces, self.total_neighborhoods
        )
        return address_data

    @staticmethod
    def _print_summary_table(il_count: int, ilce_count: int, mah_count: int) -> None:
        """Özet sayıları yatay tabloda gösterir (1. satır kategori, 2. satır adet)."""
        headers = ("İl", "İlçe", "Mahalle")
        counts = (il_count, ilce_count, mah_count)
        col_w = tuple(
            max(len(h), len(str(n))) for h, n in zip(headers, counts)
        )
        inner = "+".join("-" * (w + 2) for w in col_w)
        sep = "+" + inner + "+"

        def row_line(cells: tuple[Any, ...], widths: tuple[int, ...], numbers: bool) -> str:
            parts: List[str] = []
            for cell, w in zip(cells, widths):
                s = str(cell)
                pad = f"{s:>{w}}" if numbers else f"{s:<{w}}"
                parts.append(f" {pad} ")
            return "|" + "|".join(parts) + "|"

        print(sep)
        print(row_line(headers, col_w, numbers=False))
        print(sep)
        print(row_line(counts, col_w, numbers=True))
        print(sep)

    def save_to_file(self, data: List[Dict[str, Any]], filename: str) -> None:
        ptt_dir = "PTT"
        os.makedirs(ptt_dir, exist_ok=True)
        filepath = os.path.join(ptt_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def update_readme(
        self,
        readme_path: str = "README.md",
        *,
        il_count: Optional[int] = None,
        ilce_count: Optional[int] = None,
        mah_count: Optional[int] = None,
    ) -> None:
        if not os.path.exists(readme_path):
            print(f"README dosyası bulunamadı: {readme_path}")
            return

        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read()

        now = datetime.now()
        turkish_months = [
            "Ocak",
            "Şubat",
            "Mart",
            "Nisan",
            "Mayıs",
            "Haziran",
            "Temmuz",
            "Ağustos",
            "Eylül",
            "Ekim",
            "Kasım",
            "Aralık",
        ]
        formatted_date = (
            f"{now.day} {turkish_months[now.month - 1]} {now.year}, "
            f"{now.hour:02d}:{now.minute:02d}"
        )

        last_updated_pattern = (
            r"(## 📅 Son Güncelleme\s*\n\s*\*\*Son güncelleme:\*\*)[^\n]+"
        )
        readme_content = re.sub(
            last_updated_pattern,
            rf"\1 {formatted_date}",
            readme_content,
            flags=re.MULTILINE,
        )

        stats_note = ""
        if il_count is not None and ilce_count is not None and mah_count is not None:
            stats_block = (
                "<!-- PTT_STATS_TABLE_START -->\n"
                "| İl | İlçe | Mahalle |\n"
                "| ---: | ---: | ---: |\n"
                f"| {il_count} | {ilce_count} | {mah_count} |\n"
                "<!-- PTT_STATS_TABLE_END -->"
            )
            stats_pattern = re.compile(
                r"<!-- PTT_STATS_TABLE_START -->.*?<!-- PTT_STATS_TABLE_END -->",
                re.DOTALL,
            )
            if stats_pattern.search(readme_content):
                readme_content = stats_pattern.sub(stats_block, readme_content, count=1)
                stats_note = (
                    f"; veri özeti: {il_count} il, {ilce_count} ilçe, "
                    f"{mah_count} mahalle"
                )
            else:
                print(
                    "README: PTT_STATS_TABLE işaretçileri bulunamadı; "
                    "özet tablosu atlandı."
                )

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        print(
            f"README güncellendi: son güncelleme {formatted_date}{stats_note}"
        )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="PTT API v2 adres çekici")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="API yeniden denemelerinde ayrıntılı log",
    )
    args = parser.parse_args()

    scraper = PTTAddressApiScraper(verbose=args.verbose)
    try:
        address_data = scraper.scrape()
        filename = "ptt_il_ilce_mahalle.json"
        scraper.save_to_file(address_data, filename)
        print(f"\nVeriler PTT/{filename} dosyasına kaydedildi.")
        scraper.update_readme(
            il_count=scraper.total_states,
            ilce_count=scraper.total_provinces,
            mah_count=scraper.total_neighborhoods,
        )
    except Exception as e:
        print(f"Hata: {e}")
        raise


if __name__ == "__main__":
    main()
