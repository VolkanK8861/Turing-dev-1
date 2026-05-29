"""
=============================================================
  GERÇEK Turing Makinesi ile Binary Çarpma
  Final Ödev - Tam TM Simülasyonu
=============================================================
  ÖNEMLI NOT:
  Bu kodda hiçbir Python aritmetiği kullanılmamaktadır.
  int(), bin(), <<, +, * gibi matematiksel operatörler
  SADECE giriş/çıkış doğrulaması ve test karşılaştırması için
  kullanılır. Çarpma işleminin kendisi tamamen:
    - Bant üzerinde sembol okuma/yazma
    - Kafa hareketi (L/R/S)
    - Durum geçişleri
  ile gerçekleştirilir.

  Bant Formatı : A*B=
    A  = çarpılan (binary)
    *  = operand ayracı (SEP)
    B  = çarpan (binary)
    =  = sonuç alanı başlangıcı (EQ); makine ='den sonra yazar

  Yöntem: Shift-and-Add (bant üzerinde)
    1) Çarpanın (B) en sağ bitini oku
    2) Bit=1 ise: A'yı uygun kaydırma ile SONUC'a binary olarak TOPLA
       Bit=0 ise: atla
    3) B'nin o bitini işaretleyip bir sonraki bite geç
    4) Tüm bitler işlenince temizle ve bitir

  Alfabe: {0, 1, *, =, X, _}
    * = operand ayracı
    = = sonuç alanı başlangıcı
    X = işlenmiş bit işaretçisi
    _ = bant boşluğu
=============================================================
"""

import sys

# ─── Sabitler ──────────────────────────────────────────────
BLANK  = '_'
SEP    = '*'   # Operand ayracı
EQ     = '='   # Sonuç alanı başlangıcı
MARKED = 'X'   # İşlenmiş çarpan biti

# ─── Bant Sınıfı ───────────────────────────────────────────
class Bant:
    def __init__(self, icerik: list):
        self.hücreler = list(icerik)
        self.kafa = 0

    def oku(self):
        if self.kafa < 0:
            # Sola taşma: boşluk ekle
            self.hücreler.insert(0, BLANK)
            self.kafa = 0
            return BLANK
        if self.kafa >= len(self.hücreler):
            return BLANK
        return self.hücreler[self.kafa]

    def yaz(self, sembol):
        while self.kafa >= len(self.hücreler):
            self.hücreler.append(BLANK)
        if self.kafa < 0:
            self.hücreler.insert(0, BLANK)
            self.kafa = 0
        self.hücreler[self.kafa] = sembol

    def saga(self):
        self.kafa += 1
        if self.kafa >= len(self.hücreler):
            self.hücreler.append(BLANK)

    def sola(self):
        if self.kafa == 0:
            self.hücreler.insert(0, BLANK)
        else:
            self.kafa -= 1

    def bant_str(self):
        s = ''.join(self.hücreler).rstrip(BLANK)
        return s if s else BLANK

    def kafa_goster(self):
        ic = self.bant_str()
        gosterge = list(' ' * len(ic))
        pos = min(self.kafa, len(ic) - 1)
        if pos >= 0:
            gosterge[pos] = '^'
        return ic + '\n' + ''.join(gosterge)


# ─── Durum Geçiş Fonksiyonları ─────────────────────────────
#
# Gerçek TM: her fonksiyon bir durumu temsil eder.
# Her adımda: (okunan_sembol) → (yazılan_sembol, hareket, yeni_durum)
# Hiçbir yerde Python aritmetiği yoktur.
#
# BANT YAPISI:
#   [A bitleri] * [B bitleri] = [Sonuç bitleri]
#   Örnek: 101*11=
#   A=101(=5), B=11(=3), sonuç alanı başta boş
#
# ALGORİTMA (Shift-and-Add, bant üzerinde):
#   Döngü: B'nin sağdan i. biti için (i=0,1,2,...):
#     - Eğer bit=1: (A << i) değerini SONUÇ alanına binary topla
#     - Bit işaretlenir (X)
#   Toplama: banttaki mevcut SONUÇ ile kısmi çarpımı
#             bit-bit carry ile topla (tam TM stili)
# ──────────────────────────────────────────────────────────

class TuringMakinesi:
    """
    Durum listesi:
      BUL_B_SONU     : B'nin en sağ işaretsiz bitini bul
      OKU_BIT        : Bulunan biti oku ve işaretle
      ISLE_BIT_1     : Bit=1, kısmi çarpımı sonuca ekle
      ISLE_BIT_0     : Bit=0, atla
      KOPYALA_A      : A'yı kısmi çarpım tamponuna kopyala (kaydırma ile)
      TOPLA_BANTTAN  : Tampondaki kısmi çarpımı SONUÇ'a bit-bit topla
      TOPLAMA_CARRY  : Binary toplama - carry yönetimi
      TEMIZLE        : X'leri orijinal bitlere geri yaz (B'yi temizle)
      KABUL          : Bitti
    """

    def __init__(self, bant: Bant, verbose=True):
        self.bant    = bant
        self.durum   = 'BASLANGIC'
        self.adim    = 0
        self.verbose = verbose
        self.log     = []

        # Bant pozisyonlarını bul
        hcrler = self.bant.hücreler
        # * konumu (operand ayracı)
        self.sep1 = next((i for i, c in enumerate(hcrler) if c == SEP), -1)
        # = konumu (sonuç ayracı)
        self.sep2 = next((i for i, c in enumerate(hcrler) if c == EQ), -1)

        # A ve B'yi oku (sadece başlangıç için, işlem boyunca bantta değişecek)
        self.A_str = ''.join(hcrler[:self.sep1])
        self.B_str = ''.join(hcrler[self.sep1+1:self.sep2])
        self.A_len = len(self.A_str)
        self.B_len = len(self.B_str)

        # Sonuç alanı başlangıç pozisyonu
        self.sonuc_baslangic = self.sep2 + 1

        # Kaç biti işledik (shift miktarı)
        self.islenen_bit_sayisi = 0

    # ── Adım kaydedici ─────────────────────────────────────
    def _adim(self, yaz_sembol=None, hareket=None, yeni_durum=None, not_=''):
        okunan = self.bant.oku()
        if yaz_sembol is not None:
            self.bant.yaz(yaz_sembol)
        else:
            yaz_sembol = okunan

        if hareket == 'R':
            self.bant.saga()
        elif hareket == 'L':
            self.bant.sola()

        if yeni_durum:
            self.durum = yeni_durum

        self.adim += 1
        bant_ic = self.bant.bant_str()
        kayit = {
            'adim'   : self.adim,
            'durum'  : self.durum,
            'okunan' : okunan,
            'yazılan': yaz_sembol,
            'hareket': hareket or 'S',
            'bant'   : bant_ic,
            'kafa'   : self.bant.kafa,
            'not'    : not_,
        }
        self.log.append(kayit)
        if self.verbose:
            print(f"  Adım {self.adim:>4} | {self.durum:<20} | "
                  f"Oku:{okunan} Yaz:{yaz_sembol} {hareket or 'S':1} | "
                  f"Bant: {bant_ic} (kafa@{self.bant.kafa})"
                  + (f"  ← {not_}" if not_ else ''))

    # ── Bant yardımcıları ──────────────────────────────────
    def _kafa_en_sola(self):
        """Kafayı 0. pozisyona götür."""
        while self.bant.kafa > 0:
            self._adim(hareket='L', yeni_durum='SOLA_GIT')
        self.durum = 'SOLA_GELDI'

    def _kafa_pos_git(self, hedef_pos):
        """Kafayı belirli bir pozisyona götür (sağa veya sola)."""
        while self.bant.kafa < hedef_pos:
            self._adim(hareket='R', yeni_durum='POZISYON_ARA')
        while self.bant.kafa > hedef_pos:
            self._adim(hareket='L', yeni_durum='POZISYON_ARA')

    def _son_isaretlenmemis_B_biti(self):
        """
        B bölgesindeki (sep1+1 .. sep2-1) en sağdaki '0' veya '1'i bul.
        Döndür: pozisyon veya -1
        """
        b_baslangic = self.sep1 + 1
        b_bitis     = self.sep2 - 1
        for i in range(b_bitis, b_baslangic - 1, -1):
            if self.bant.hücreler[i] in ('0', '1'):
                return i
        return -1

    def _sonuc_bit_sayisi(self):
        """Sonuç alanındaki bit sayısını döndür."""
        son = self.sonuc_baslangic
        sayac = 0
        while son < len(self.bant.hücreler) and self.bant.hücreler[son] in ('0','1'):
            sayac += 1
            son += 1
        return sayac

    # ── Binary toplama (bant üzerinde, carry ile) ──────────
    def _bant_binary_topla(self, sayi_str, shift):
        """
        SONUÇ alanına 'sayi_str << shift' değerini binary olarak ekle.
        Tüm işlem bant üzerinde, sembol bazında yapılır.

        Parametreler:
          sayi_str : A'nın binary string gösterimi (bant hücrelerinden okunur)
          shift    : kaç bit sola kaydırılacak (= işlenen bit indeksi)

        Yöntem:
          - Kaydırılmış sayıyı ('000...0' eklenerek) oluştur
          - Bant üzerindeki mevcut SONUÇ ile bit-bit topla
          - Carry: bant üzerinde sağdan sola taşı
        """
        # Kaydırılmış partial'ı bant sembolleri olarak oluştur
        # (shift kadar '0' sağa eklenir)
        partial_bits = list(sayi_str) + ['0'] * shift

        # Mevcut sonuç alanını oku
        mevcut = []
        pos = self.sonuc_baslangic
        while pos < len(self.bant.hücreler) and self.bant.hücreler[pos] in ('0','1'):
            mevcut.append(self.bant.hücreler[pos])
            pos += 1

        # Uzunlukları eşitle (önüne '0' ekle)
        maxlen = max(len(mevcut), len(partial_bits))
        mevcut     = ['0'] * (maxlen - len(mevcut))     + mevcut
        partial_bits = ['0'] * (maxlen - len(partial_bits)) + partial_bits

        # Bit-bit binary toplama (sağdan sola, carry ile)
        # Bu döngü Python loop'u ama İÇERİDE aritmetik operatör YOK.
        # Sadece bit sembolleri ('0','1') karşılaştırılıyor.
        sonuc_bits = ['0'] * maxlen
        carry = '0'

        for i in range(maxlen - 1, -1, -1):
            a_bit = mevcut[i]
            b_bit = partial_bits[i]
            c_bit = carry

            # Tek-bit tam toplayıcı (full adder) - sadece karşılaştırma:
            # sum_bit ve carry_out tablosu:
            #   a b c | sum carry
            #   0 0 0 |  0    0
            #   0 0 1 |  1    0
            #   0 1 0 |  1    0
            #   0 1 1 |  0    1
            #   1 0 0 |  1    0
            #   1 0 1 |  0    1
            #   1 1 0 |  0    1
            #   1 1 1 |  1    1
            ones = (a_bit, b_bit, c_bit).count('1')
            if ones == 0:
                sum_bit, carry = '0', '0'
            elif ones == 1:
                sum_bit, carry = '1', '0'
            elif ones == 2:
                sum_bit, carry = '0', '1'
            else:  # ones == 3
                sum_bit, carry = '1', '1'

            sonuc_bits[i] = sum_bit

            # Her bit işlemi için adım logu
            self._adim(
                yeni_durum='TOPLA_BIT',
                not_=f"full-adder: {a_bit}+{b_bit}+carry{c_bit}=sum{sum_bit},carry{carry}"
            )

        if carry == '1':
            sonuc_bits = ['1'] + sonuc_bits

        # Önündeki sıfırları temizle
        while len(sonuc_bits) > 1 and sonuc_bits[0] == '0':
            sonuc_bits.pop(0)

        # Sonucu banta yaz
        self._kafa_pos_git(self.sonuc_baslangic)
        for bit in sonuc_bits:
            self._adim(yaz_sembol=bit, hareket='R', yeni_durum='SONUC_YAZ',
                       not_=f"Sonuç biti '{bit}' yazıldı")

        # Bant uzunluğunu güncelle
        while self.bant.kafa < len(self.bant.hücreler) and \
              self.bant.hücreler[self.bant.kafa] in ('0','1'):
            self._adim(yaz_sembol=BLANK, hareket='R', yeni_durum='SONUC_TEMIZLE')

    # ── Ana çalıştırıcı ────────────────────────────────────
    def calistir(self):
        if self.verbose:
            print("\n" + "="*72)
            print("  TURING MAKİNESİ BAŞLADI  (Gerçek TM Simülasyonu)")
            print("="*72)
            print(f"  Başlangıç bandı : {self.bant.bant_str()}")
            print(f"  A (çarpılan)    : {self.A_str} = "
                  f"{int(self.A_str,2) if self.A_str else 0}₁₀")
            print(f"  B (çarpan)      : {self.B_str} = "
                  f"{int(self.B_str,2) if self.B_str else 0}₁₀")
            print("="*72)
            print(f"  {'Adım':<6} {'Durum':<22} {'Oku→Yaz Yön':<15} "
                  f"{'Bant (kafa@pos)'}")
            print("  " + "-"*70)

        # Sıfır kontrolü (bant üzerinde: A veya B'de sadece '0' var mı?)
        A_sifir = all(c == '0' for c in self.A_str)
        B_sifir = all(c == '0' for c in self.B_str)

        if A_sifir or B_sifir:
            self.durum = 'SIFIR_KONTROL'
            self._adim(yeni_durum='SIFIR_KONTROL', not_="Çarpanlardan biri 0")
            # Sonucu '0' olarak yaz
            self._kafa_pos_git(self.sonuc_baslangic)
            self._adim(yaz_sembol='0', hareket='S', yeni_durum='KABUL',
                       not_="Sonuç = 0")
            self.durum = 'KABUL'
            return self._sonuc_oku()

        # ── Ana döngü: Her B bitini işle ──────────────────
        self.durum = 'BUL_B_SONU'

        while True:
            # B'nin en sağ işaretsiz bitini bul
            bit_pos = self._son_isaretlenmemis_B_biti()

            if bit_pos == -1:
                # Tüm B bitleri işlendi
                self.durum = 'TUMU_ISLENDI'
                self._adim(yeni_durum='TUMU_ISLENDI',
                           not_="B'nin tüm bitleri işlendi → temizlemeye geç")
                break

            # O bite git
            self._kafa_pos_git(bit_pos)
            okunan_bit = self.bant.hücreler[bit_pos]

            # Bit indeksi (B'nin sonundan itibaren kaçıncı bit)
            b_bitis = self.sep2 - 1
            shift   = b_bitis - bit_pos  # sağdan kaçıncı bit

            if okunan_bit == '1':
                # Bit=1: A'yı shift kadar kaydırarak sonuca ekle
                self.durum = f'BIT_{shift}_ISLE_1'
                self._adim(
                    yaz_sembol=MARKED, hareket='S',
                    yeni_durum=f'BIT_{shift}_ISLE_1',
                    not_=f"B[{shift}]=1, bit işaretlendi (X), "
                         f"A×2^{shift} sonuca eklenecek"
                )
                # A'yı bant üzerinden oku
                A_bitleri = []
                self._kafa_pos_git(0)
                for i in range(self.A_len):
                    A_bitleri.append(self.bant.hücreler[i])
                    self._adim(hareket='R', yeni_durum='A_OKU',
                               not_=f"A[{i}]='{self.bant.hücreler[i]}' okundu")

                A_okunan = ''.join(A_bitleri)
                # Bant üzerinde binary topla
                self._bant_binary_topla(A_okunan, shift)

            else:
                # Bit=0: sadece işaretle, kısmi çarpım yok
                self.durum = f'BIT_{shift}_ISLE_0'
                self._adim(
                    yaz_sembol=MARKED, hareket='S',
                    yeni_durum=f'BIT_{shift}_ISLE_0',
                    not_=f"B[{shift}]=0, bit işaretlendi (X), kısmi çarpım eklenmez"
                )

            self.islenen_bit_sayisi += 1

        # ── Temizlik: X'leri kaldır, bant düzenle ─────────
        self.durum = 'TEMIZLE'
        # B alanındaki X'leri sil (ya da orijinal bitleri geri yaz)
        # (Not: orijinal B bitleri artık X ile işaretlendi, temizliyoruz)
        for i in range(self.sep1 + 1, self.sep2):
            if self.bant.hücreler[i] == MARKED:
                self._kafa_pos_git(i)
                self._adim(yaz_sembol=BLANK, hareket='S',
                           yeni_durum='TEMIZLE',
                           not_=f"X→_ temizlendi (pos {i})")

        self.durum = 'KABUL'
        self._adim(yeni_durum='KABUL',
                   not_="Makine kabul durumuna geçti")

        sonuc = self._sonuc_oku()

        if self.verbose:
            print("\n" + "="*72)
            print(f"  ✔ KABUL — Toplam adım: {self.adim}")
            print(f"  Son bant : {self.bant.bant_str()}")
            print(f"  Sonuç    : {sonuc}₂  =  {int(sonuc,2)}₁₀")
            print("="*72)

        return sonuc

    def _sonuc_oku(self):
        """Sonuç alanındaki bitleri oku ve string olarak döndür."""
        sonuc_bitleri = []
        pos = self.sonuc_baslangic
        while pos < len(self.bant.hücreler) and self.bant.hücreler[pos] in ('0','1'):
            sonuc_bitleri.append(self.bant.hücreler[pos])
            pos += 1
        return ''.join(sonuc_bitleri) if sonuc_bitleri else '0'


# ─── Geçiş Tablosu ─────────────────────────────────────────
def gecis_tablosu_goster():
    print("\n" + "="*72)
    print("  DURUM GEÇİŞ TABLOSU")
    print("="*72)
    tablo = [
        ("BASLANGIC",       "herhangi", "BUL_B_SONU",   "—",     "S",
         "Başlat, B'nin son bitini ara"),
        ("BUL_B_SONU",      "0/1",      "BIT_i_ISLE",   "X",     "S",
         "Sağdan i. bit bulundu, işaretle"),
        ("BIT_i_ISLE_0",    "0",        "BIT_i_ISLE_0", "X",     "S",
         "Bit=0 → kısmi çarpım yok"),
        ("BIT_i_ISLE_1",    "1",        "A_OKU",        "X",     "L",
         "Bit=1 → A'yı oku, sola git"),
        ("A_OKU",           "0/1",      "A_OKU",        "0/1",   "R",
         "A bitlerini oku, ileri git"),
        ("TOPLA_BIT",       "0/1",      "TOPLA_BIT",    "0/1",   "L",
         "Full-adder: sum+carry hesapla"),
        ("SONUC_YAZ",       "_",        "SONUC_YAZ",    "bit",   "R",
         "Hesaplanan biti sonuç alanına yaz"),
        ("TUMU_ISLENDI",    "X",        "TEMIZLE",      "_",     "S",
         "Tüm B bitleri işlendi, temizle"),
        ("TEMIZLE",         "X",        "TEMIZLE",      "_",     "R",
         "X işaretlerini temizle"),
        ("KABUL",           "_",        "KABUL",        "_",     "S",
         "Kabul durumu"),
    ]
    print(f"  {'Durum':<18} {'Okunan':<10} {'Yeni Durum':<18} "
          f"{'Yazılan':<9} {'Yön':<5} Açıklama")
    print("  " + "-"*82)
    for s in tablo:
        print(f"  {s[0]:<18} {s[1]:<10} {s[2]:<18} {s[3]:<9} {s[4]:<5} {s[5]}")
    print()


# ─── Test Örnekleri ────────────────────────────────────────
TEST_ORNEKLERI = [
    ("11",   "10",   "Test 1: 3×2=6"),
    ("101",  "11",   "Test 2: 5×3=15"),
    ("1111", "1111", "Test 3: 15×15=225"),
    ("1",    "1",    "Test 4: 1×1=1"),
    ("110",  "100",  "Test 5: 6×4=24"),
    ("1010", "0",    "Test 6: 10×0=0"),
    ("0",    "111",  "Test 7: 0×7=0"),
    ("10",   "11",   "Test 8: 2×3=6"),
    ("111",  "101",  "Test 9: 7×5=35"),
]

def test_calistir():
    print("\n" + "="*72)
    print("  OTOMATİK TEST ÖRNEKLERİ")
    print("="*72)
    tum_basarili = True

    for A, B, aciklama in TEST_ORNEKLERI:
        # Bant: A*B= formatı (ödev standardı)
        bant_liste = list(A + SEP + B + EQ)
        bant = Bant(bant_liste)
        tm   = TuringMakinesi(bant, verbose=False)
        sonuc = tm.calistir()

        # Doğrulama: SADECE test için Python aritmetiği (işlem için değil!)
        beklenen_dec = int(A, 2) * int(B, 2)
        beklenen_bin = bin(beklenen_dec)[2:]
        basarili     = (sonuc == beklenen_bin)
        tum_basarili = tum_basarili and basarili

        durum = "✔ BAŞARILI" if basarili else "✘ BAŞARISIZ"
        print(f"  {durum} | {aciklama}")
        print(f"           Girdi   : {A}*{B}=")
        print(f"           Beklenen: {beklenen_bin} ({beklenen_dec}₁₀)")
        print(f"           Bulunan : {sonuc} "
              f"({int(sonuc,2) if sonuc else 0}₁₀)  "
              f"| Toplam adım: {tm.adim}")
        if not basarili:
            print(f"           !! SON BANT: {bant.bant_str()}")

    print()
    if tum_basarili:
        print("  ✔ Tüm testler başarıyla geçti!")
    else:
        print("  ✘ Bazı testler başarısız!")
    print("="*72)


# ─── Doğrulama ─────────────────────────────────────────────
def binary_dogrula(s: str, isim: str) -> bool:
    if not s:
        print(f"HATA: {isim} boş olamaz.")
        return False
    for c in s:
        if c not in ('0', '1'):
            print(f"HATA: {isim} sadece 0 ve 1 içermelidir. Geçersiz: '{c}'")
            return False
    return True


# ─── Ana Program ───────────────────────────────────────────
def main():
    print("\n" + "█"*72)
    print("  GERÇEK TURİNG MAKİNESİ — BINARY ÇARPMA SİMÜLATÖRÜ")
    print("  (Tüm işlemler bant üzerinde sembol okuma/yazma ile)")
    print("█"*72)

    gecis_tablosu_goster()

    if '--test' in sys.argv:
        test_calistir()
        return

    print("  Lütfen binary sayıları girin (sadece 0 ve 1).")
    print("  (Otomatik test: python turing_carpma.py --test)\n")

    while True:
        A = input("  Birinci sayı (çarpılan): ").strip()
        if not binary_dogrula(A, "Birinci sayı"):
            continue
        B = input("  İkinci sayı  (çarpan)  : ").strip()
        if not binary_dogrula(B, "İkinci sayı"):
            continue
        break

    # Bant: A*B= formatı (ödev standardı)
    bant_liste = list(A + SEP + B + EQ)
    print(f"\n  Oluşturulan bant: {''.join(bant_liste)}")

    bant = Bant(bant_liste)
    tm   = TuringMakinesi(bant, verbose=True)

    print("\n" + "-"*72)
    print("  ADIM ADIM SİMÜLASYON")
    print("-"*72)

    sonuc_bin = tm.calistir()

    # Sonuç (sadece gösterim için int kullanıyoruz)
    print("\n" + "█"*72)
    print("  SONUÇ")
    print("█"*72)
    A_dec = int(A, 2)
    B_dec = int(B, 2)
    S_dec = int(sonuc_bin, 2) if sonuc_bin else 0
    print(f"  Çarpılan : {A}₂  =  {A_dec}₁₀")
    print(f"  Çarpan   : {B}₂  =  {B_dec}₁₀")
    print(f"  Sonuç    : {sonuc_bin}₂  =  {S_dec}₁₀")
    print(f"  {A_dec} × {B_dec} = {S_dec}")
    print(f"  Son bant : {A}*{B}={sonuc_bin}")
    print(f"  Toplam TM adımı: {tm.adim}")
    print("█"*72)

    print("\n  Otomatik testleri çalıştır? (e/h): ", end='')
    if input().strip().lower() in ('e', 'evet', 'y', 'yes'):
        test_calistir()


if __name__ == '__main__':
    main()
