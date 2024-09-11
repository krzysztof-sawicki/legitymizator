# Legitymizator
Program ułatwiający przygotowywanie Elektronicznych Legitymacji Szkolnych (ELS) do wydruku na blankietach w formacie ID-1 ISO/IEC 7810. Ułożenie pól na legitymacji jest zgodne ze wzorami z [załącznika nr 4 do Rozporządzenia Ministra Edukacji i Nauki z dnia 7 czerwca 2023 r. w sprawie świadectw, dyplomów państwowych i innych druków](https://www.dziennikustaw.gov.pl/DU/2023/1120):
- MEiN-I/1,
- MEiN-I/2,
- MEiN-I/3-N,
- MEiN-I/4-N.

Program napisany jest w języku Python i korzysta z biblioteki [wxWidgets](https://wxwidgets.org/) (implementacja [wxPython](https://wxpython.org/)).

Wersja 0.1 jest wstępną wersją, napisaną na szybko, z mnóstwem "dirty-hacków". Testowane tylko pod Linuksem. Możliwe, że zadziała pod Windows z niewielkimi zmianami (m.in. wskazanie pliku z czcionką w StudentID.py). 

## Wymagania
1. Python w wersji min. 3.8 z zainstalowanymi pakietami:
	- defusedxml==0.7.1
    - fonttools==4.53.1
    - fpdf2==2.7.9
    - numpy==2.1.1
    - pdf2image==1.17.0
    - pillow==10.4.0
    - PyMuPDF==1.24.10
    - PyMuPDFb==1.24.10
    - PyPDF2==3.0.1
    - six==1.16.0
    - wxPython==4.2.1 
2.  W najnowszej wersji wxPython (aktualnie 4.2.1) konieczna jest niewielka poprawka w pliku wx/lib/pdfviewer/viewer.py. W linijce 1080 należy zamienić treść `self.FitThisSizeToPage(wx.Size(width*sfac, height*sfac))` na `self.FitThisSizeToPage(wx.Size(int(width*sfac), int(height*sfac)))` zgodnie z [poprawką](https://github.com/wxWidgets/Phoenix/commit/0cf08c27fd6f9152c86879da042d8ca7e3af4f1d). Bez tej poprawki nie będzie działało wysyłanie przygotowanego pliku PDF do drukarki.
3.  Do modyfikacji interfejsu warto posiadać [wxGlade](https://github.com/wxGlade/wxGlade).

## Uruchamianie
`$ python3 Legitymizator.py`
lub
`$ ./Legitymizator.py` po wcześniejszych dodaniu prawa do wykonania `chmod a+x Legitymizator.py`

## Uwagi praktyczne
- Dane przechowywane są w pliku bazy danych SQLite. W bazie danych przechowywane jest również załadowane zdjęcie. Rozmiar pliku bazy danych, z tego powodu, może być znaczny.
- Pliki PDF z wygenerowanym obrazem legitymacji do nadruku na blankiecie przygotowanym przez [PWPW](https://www.pwpw.pl/Produkty/Karty/Karty_komercyjne.html) są zapisywane w tym samym katalogu, w którym jest zapisywana baza danych.
- Zdjęcie do nadruku musi mieć rozmiar min. 225x307 pikseli (300 DPI).
