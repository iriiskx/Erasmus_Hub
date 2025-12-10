# 🎓 Erasmus+ Hub

Plnofunkčná webová aplikácia pre správu programu Erasmus+ vyvinutá na Flask frameworku.

## 📋 Obsah

- [O projekte](#-o-projekte)
- [Funkcie](#-funkcie)
- [Inštalácia](#-inštalácia)
- [Štruktúra projektu](#-štruktúra-projektu)
- [Použitie](#-použitie)
- [Technológie](#-technológie)
- [API a smerovanie](#-api-a-smerovanie)
- [Bezpečnosť](#-bezpečnosť)

## 🎯 O projekte

Erasmus+ Hub je komplexný systém pre správu študentských prihlášok na mobilitu v rámci programu Erasmus+. Aplikácia poskytuje plnohodnotné rozhranie pre študentov aj administrátorov s možnosťou správy prihlášok, dokumentov, oznámení a štatistík.

## ✨ Funkcie

### 🔐 Autentifikácia a autorizácia
- ✅ Registrácia používateľov (študenti a administrátori)
- ✅ Prihlásenie/Odhlásenie z systému
- ✅ Rôzne úrovne prístupu (študent/admin)
- ✅ Ochrana trás podľa rolí
- ✅ Hashovanie hesiel (Werkzeug PBKDF2)
- ✅ Sessiónová autentifikácia s časovým limitom (24 hodín)

### 👨‍🎓 Študentský panel
- ✅ Vytváranie nových prihlášok na mobilitu
- ✅ Nahrávanie dokumentov
- ✅ Prehľad vlastných prihlášok
- ✅ Aktualizácia dokumentov v prihláške
- ✅ Prehľad stavov dokumentov
- ✅ Prehľad oznámení a noviniek
- ✅ Úprava profilu
- ✅ Sťahovanie súborov
- ✅ Prehľad komentárov administrátora

### 👨‍💼 Administrátorský panel
- ✅ Hlavná štatistická stránka
- ✅ Správa prihlášok (prehľad, schválenie, zamietnutie)
- ✅ Komentovanie prihlášok
- ✅ Správa stavov dokumentov
- ✅ Správa používateľov
- ✅ Správa oznámení (CRUD operácie)
- ✅ Detailná štatistika
- ✅ Vyhľadávanie a filtrovanie prihlášok
- ✅ Filtrovanie podľa študenta, statusu a vyhľadávacieho dotazu

### 💾 Databáza
- ✅ SQLite databáza
- ✅ Tabuľky: users, applications, documents, application_comments, messages, announcements
- ✅ Automatická migrácia z JSON súborov
- ✅ Plné CRUD operácie pre všetky entity
- ✅ Referenčná integrita (Foreign Keys)
- ✅ Kaskádové mazanie

### 📊 Štatistiky
- ✅ Štatistiky podľa mesiacov
- ✅ Štatistiky podľa typov mobility
- ✅ Štatistiky dokumentov
- ✅ Celkové počty prihlášok a študentov

## 🚀 Inštalácia

### Požiadavky
- Python 3.8 alebo vyšší
- pip (správca balíčkov Python)

### Kroky inštalácie

1. **Naklonujte alebo stiahnite projekt:**
```bash
cd erasmus_hub
```

2. **Vytvorte virtuálne prostredie (odporúčané):**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Nainštalujte závislosti:**
```bash
pip install -r requirements.txt
```

4. **Spustite aplikáciu:**
```bash
python app.py
```

5. **Otvorte prehliadač:**
```
http://localhost:5000
```

### Prvé spustenie

Pri prvom spustení sa automaticky:
- Vytvorí SQLite databáza (`erasmus_hub.db`)
- Vytvoria sa všetky potrebné tabuľky
- Vytvoria sa predvolení používatelia (ak databáza je prázdna)
- Vykoná sa migrácia dát z JSON súborov (ak existujú)

## 📁 Štruktúra projektu

```
erasmus_hub/
├── app.py                      # Hlavný Flask aplikácia
├── database.py                 # Inicializácia DB a migrácia
├── models.py                  # Modely pre prácu s databázou
├── config.py                  # Konfigurácia aplikácie
├── requirements.txt           # Python závislosti
├── erasmus_hub.db             # SQLite databáza (vytvorí sa automaticky)
├── templates/                 # HTML šablóny
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── student_dashboard.html
│   ├── student_profile.html
│   ├── student_view_application.html
│   ├── student_announcements.html
│   ├── application_form.html
│   ├── update_documents.html
│   ├── admin_panel.html
│   ├── admin_view_application.html
│   ├── admin_announcement_form.html
│   ├── admin_users.html
│   └── admin_statistics.html
└── static/                    # Statické súbory
    ├── css/
    │   └── styles.css
    └── uploads/               # Nahrané súbory
```

## 💻 Použitie

### Predvolení používatelia

Po prvom spustení sú k dispozícii tieto účty:

**Študent:**
- Email: `student@example.com`
- Heslo: `student`

**Administrátor:**
- Email: `admin@example.com`
- Heslo: `admin`

⚠️ **Dôležité:** V produkčnom prostredí zmeňte tieto predvolené údaje!

### Typy dokumentov

Aplikácia podporuje 7 typov povinných dokumentov:
1. Životopis (v angličtine)
2. Motivačný list (v angličtine)
3. Výpis známok potvrdený fakultou
4. Predpokladaný študijný plán
5. Osvedčenie o jazykových znalostiach
6. Kópia pasu (zahraniční študenti)
7. Iné – doplňujúce dokumenty

### Statusy prihlášok

- **Podaná** - Prihláška bola odoslaná a čaká na posúdenie
- **Schválená** - Prihláška bola schválená administrátorom
- **Zamietnutá** - Prihláška bola zamietnutá (s dôvodom)

### Statusy dokumentov

- **Odoslaný** - Dokument bol nahraný
- **V preverovaní** - Dokument je v procese kontroly
- **Schválený** - Dokument bol schválený
- **Zamietnutý** - Dokument bol zamietnutý

## 🔧 Technológie

- **Flask 3.0.3** - Webový framework
- **SQLite** - Databázový systém
- **Bootstrap 5.3.2** - Frontend framework
- **Werkzeug** - Bezpečnosť (hashovanie hesiel)
- **Jinja2** - Šablónovací systém

## 🛣️ API a smerovanie

### Verejné trasy
- `GET /` - Hlavná stránka
- `GET/POST /login` - Prihlásenie
- `GET/POST /register` - Registrácia
- `GET /logout` - Odhlásenie

### Študentské trasy
- `GET /student` - Študentský panel
- `GET/POST /student/profile` - Profil študenta
- `GET /student/application/<id>` - Detaily prihlášky
- `GET /student/announcements` - Oznámenia
- `GET/POST /application` - Vytvorenie prihlášky
- `GET/POST /student/application/<id>/update-documents` - Aktualizácia dokumentov
- `POST /applications/<id>/delete` - Zmazanie prihlášky

### Administrátorské trasy
- `GET /admin` - Administrátorský panel
- `GET /admin/applications/<id>` - Detaily prihlášky
- `POST /admin/applications/<id>/approve` - Schválenie prihlášky
- `POST /admin/applications/<id>/reject` - Zamietnutie prihlášky
- `POST /admin/applications/<id>/comment` - Pridanie komentára
- `GET/POST /admin/announcements/new` - Nové oznámenie
- `GET/POST /admin/announcements/<id>/edit` - Úprava oznámenia
- `POST /admin/announcements/<id>/delete` - Zmazanie oznámenia
- `GET /admin/users` - Správa používateľov
- `POST /admin/users/<email>/delete` - Zmazanie používateľa
- `POST /admin/documents/<id>/update-status` - Aktualizácia statusu dokumentu
- `GET /admin/statistics` - Detailná štatistika

### Všeobecné trasy
- `GET /download/<filename>` - Sťahovanie súboru

## 🔒 Bezpečnosť

### Implementované bezpečnostné opatrenia:
- ✅ Hashovanie hesiel pomocou PBKDF2
- ✅ Ochrana trás pomocou dekorátorov (`@login_required`, `@role_required`)
- ✅ Bezpečné ukladanie súborov (secure_filename)
- ✅ Validácia vstupných dát
- ✅ Kontrola prístupu k súborom
- ✅ Sessiónová autentifikácia s časovým limitom

### Odporúčania pre produkciu:
- Zmeňte `SECRET_KEY` v `app.py`
- Použite produkčnú databázu (PostgreSQL, MySQL)
- Nastavte HTTPS
- Pravidelne aktualizujte závislosti
- Použite environment premenné pre citlivé údaje

## 📝 Poznámky

- Databáza sa vytvorí automaticky pri prvom spustení
- Súbory sa ukladajú do `static/uploads/`
- Automatická migrácia z JSON súborov sa vykoná pri štarte (ak existujú)
- Všetky časové značky sú v UTC

## 🤝 Podpora

Pre otázky alebo problémy vytvorte issue v repozitári projektu.

## 📄 Licencia

Tento projekt je vytvorený pre vzdelávacie účely.

---

**Verzia:** 1.0.0  
**Posledná aktualizácia:** 2024
