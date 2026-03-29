from fastapi import FastAPI, Request, Form, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from jinja2 import FileSystemLoader, Environment
import os
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import sqlite3
from passlib.context import CryptContext
from database import Database
from auth import router as auth_router
from phone_utils import normalize_phone, COUNTRY_CHOICES, get_country_from_e164, example_for_country, DIAL_CODES
from validators import validate_name, validate_username, validate_password, validate_phone
import random
import time
from datetime import date, timedelta, datetime

# Password hashing - must be defined before ensure_permanent_admin()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Translations dictionary
translations = {
    'hr': {
        'Home': 'Početna',
        'GPS': 'GPS praćenje',
        'Analysis': 'Analiza',
        'Profile': 'Profil',
        'Login': 'Prijavi se',
        'Signup': 'Registriraj se',
        'Welcome': 'Dobrodošao',
        'Welcome_back': 'Bok',
        'Your_effort_matters': 'Tvoj trud čini razliku.',
        'Emission': 'Emisija',
        'Savings': 'Ušteda',
        'Eco_Score': 'Eko Score',
        'Weekly_Activity': 'Tjedna Aktivnost',
        'Streak': 'Niz',
        'Days_of_eco_consciousness': 'dana eko-svijesti',
        'Start_free': 'Započni besplatno',
        'Analysis_of_results': 'Analiza Rezultata',
        'Overview_of_progress': 'Pregled tvog napretka u EcoCode sustavu.',
        'Todays_Score': 'Današnji Score',
        'CO2_Savings': 'Ušteda CO₂',
        'Status': 'Status',
        'Excellent': 'ODLIČNO',
        'Good': 'DOBRO',
        'Average': 'OSREDNJE',
        'Poor': 'LOŠE',
        'No_data': 'NEMA PODATAKA',
        'Sustainability_Trend': 'Trend Održivosti',
        'Tip_of_the_day': 'Savjet dana',
        'Biking_saves_CO2': 'Bicikliranje štedi preko 90% CO₂ u usporedbi s autom.',
        'EcoCode': 'EcoCode',
        'Dashboard': 'Nadzorna ploča',
        'Logout': 'Odjava',
        'Settings': 'Postavke',
        'Users': 'Korisnici',
        'Activities': 'Aktivnosti',
        'GPS_Tracking': 'GPS Praćenje',
        'Insights': 'Uvidi',
        'Track': 'Dnevnik',
        'Admin_Tools': 'Admin Alati',
        'Start_EcoCode': 'Pokreni EcoCode',
        'Join_community': 'Pridruži se zajednici koja aktivno mijenja svijet.',
        'Settings': 'Postavke',
        'System_Settings': 'Postavke Sustava',
        'Customize_experience': 'Prilagodite svoje iskustvo i upravljajte računom',
        'Back_to_profile': 'Povratak na profil',
        'Personal_Data': 'Osobni podaci',
        'Change_name_email': 'Promijenite ime, email, lozinku ili broj telefona',
        'Interface_Appearance': 'Izgled sučelja',
        'Switch_themes': 'Prebacite između svijetlog i tamnog načina rada',
        'Language': 'Jezik',
        'Choose_language': 'Odaberite željeni jezik aplikacije',
        'EULA': 'EULA',
        'View_terms': 'Pogledajte uvjete korištenja i pravila privatnosti',
        # Track page translations
        'Activity_Diary': 'Dnevnik aktivnosti',
        'Track_Activities': 'Prati aktivnosti 🌱',
        'Record_daily_habits': 'Zabilježi svoje dnevne navike i smanji otisak.',
        'New_Entry': 'Nova bilješka',
        'Category': 'Kategorija',
        'Subtype': 'Podtip',
        'Quantity': 'Količina',
        'CO2_kg': 'CO₂ (kg)',
        'Add': 'Dodaj',
        'Transport': 'Transport',
        'Electricity': 'Struja',
        'Water': 'Voda',
        'Food': 'Hrana',
        'Shopping': 'Kupovina',
        'History': 'Povijest zapisa',
        'Loading': 'Učitavanje...',
        'No_records_yet': 'Još nema zapisa.',
        'Total_Impact': 'Ukupni utjecaj',
        'CO2_Collected': 'CO₂ prikupljeno',
        'Tip': 'Savjet',
        'Shower_tip': 'Smanjenjem tuširanja za samo 2 minute štediš do 40 litara vode dnevno!',
        'Admin_Emission_Factors': '🛠 Admin: Emisijski faktori',
        'Add_Factor': 'Dodaj faktor',
        'Cat': 'Kat.',
        'Sub': 'Sub.',
        'Unit': 'Jed.',
        'kg_per_unit': 'kg/jed',
        'Save': 'Spremi',
        'Footer': 'EcoCode | NLimit &copy; 2026 • Čuvamo tvoj ekološki otisak 🌱',
        'Home_title': 'EcoCode - Nadzorna ploča',
        'Tap_to_unmute': 'Dodirnite za uključivanje zvuka',
        'Dark_theme': 'Tamna tema',
        'EULA_title': 'Uvjeti korištenja 🌿',
        'EULA_updated': 'Ažurirano: 24. ožujka 2026.',
        'EULA_intro': 'Dobrodošli u EcoCode, digitalni servis specijaliziran za praćenje i analizu osobnog ugljičnog otiska. EcoCode je službeni projekt razvijen unutar NLimit platforme, koja služi kao inkubator za inovativna softverska rješenja i digitalnu održivost.',
        'EULA_agreement': 'Korištenjem aplikacije EcoCode na domeni ecocode.codes ili povezanim servisima, pristajete na sljedeće uvjete:',
        'EULA_section1_title': '1. Vlasništvo i licenca',
        'EULA_section1_content': 'EcoCode je autorsko djelo i intelektualno vlasništvo unutar NLimit platforme. Korisniku se dodjeljuje pravo na osobno, nekomercijalno korištenje platforme u svrhe osvještavanja ekološke održivosti. Bilo kakav pokušaj neovlaštenog pristupa bazi podataka, modifikacija izvornog koda ili zlouporaba NLimit tehnologije strogo je zabranjena.',
        'EULA_section2_title': '2. Privatnost i GPS praćenje',
        'EULA_section2_content': 'Za pružanje preciznog izračuna, aplikacija koristi GPS koordinate korisnika isključivo za mjerenje prijeđene udaljenosti. NLimit platforma se obvezuje da se podaci o lokaciji koriste isključivo za potrebe trenutnog izračuna emisija unutar aplikacije. Vaši podaci su privatni i neće biti ustupani trećim stranama bez vaše izričite privole.',
        'EULA_section3_title': '3. Metodologija i točnost podataka',
        'EULA_section3_content': 'Izračuni emisija CO₂ unutar EcoCode servisa temelje se na općeprihvaćenim ekološkim koeficijentima (npr. prosječne emisije za putnička vozila). Ovi podaci služe kao informativni prikaz i edukativni alat. NLimit ne jamči apsolutnu znanstvenu preciznost te se ovi podaci ne smiju koristiti kao službeni certifikati u pravnim ili komercijalnim poslovima.',
        'EULA_section4_title': '4. Korisnički račun i sigurnost',
        'EULA_section4_content': 'Korisnik je odgovoran za čuvanje tajnosti svojih pristupnih podataka. NLimit preporučuje korištenje jedinstvenih lozinki radi zaštite integriteta vašeg profila i povijesti izračuna.',
        'EULA_section5_title': '5. Ograničenje odgovornosti',
        'EULA_section5_content': 'Korištenjem ovog servisa, korisnik prihvaća da NLimit platforma i njezini autori nisu odgovorni za bilo kakvu neizravnu štetu, gubitak podataka ili tehničke prekide u radu aplikacije. Servis se pruža "onakav kakav jest" u svrhu promicanja ekološke svijesti.',
        'EULA_section6_title': '6. Izmjene i budući razvoj',
        'EULA_section6_content': 'Zadržavamo pravo izmjene ovih uvjeta u skladu s tehničkim napretkom aplikacije ili promjenama u regulativama o zaštiti podataka. Budući da je EcoCode dio šireg NLimit ekosustava, korisnici će biti obaviješteni o svim značajnim nadogradnjama ili integracijama novih alata.',
        'EULA_button': 'Razumijem, nastavi',
        # Signup page translations
        'Signup_title': 'Registracija - EcoCode',
        'Become_Eco_Hero': 'Postani eko heroj 🌿',
        'Join_movement': 'Pridruži se pokretu za čišći planet.',
        'Full_Name': 'Puno ime',
        'Name_placeholder': 'Ivan Horvat',
        'Username_placeholder': 'eko_ratnik',
        'Email_Address': 'E-mail adresa',
        'Email_placeholder': 'ivan@primjer.hr',
        'Country': 'Država',
        'Phone_Number': 'Broj telefona',
        'Example': 'Primjer:',
        'Confirm_Password': 'Potvrdi lozinku',
        'Accept_EULA': 'Prihvaćam <a href="/eula?from=signup" target="_blank" style="color: #10b981; text-decoration: none; font-weight: 600;">uvjete korištenja i politiku privatnosti</a> za EcoCode.',
        'Create_Account': 'Kreiraj račun',
        'Already_have_account': 'Već imate račun? Prijavite se',
        'Show': 'Prikaži',
        'Hide': 'Sakrij',
        'Delete': 'Obriši',
        'Confirm_delete': 'Obrisati zapis?',
        # Profile page translations
        'Profile_title': 'Profil',
        'Logging_out': 'Odjavljivanje...',
        'Dashboard': 'Nadzorna ploča',
        'Settings_emoji': '⚙️ Postavke',
        'Logout': 'Odjavi se',
        'Account_Data': 'Podaci računa',
        'Email': 'E-mail',
        'Phone': 'Telefon',
        'Member_since': 'Član od',
        'Not_entered': 'Nije uneseno',
        'Not_connected': 'Nije povezano',
        'Your_effort_matters_planet': 'Tvoj trud čini razliku za planetu! 🌱',
        # Daily CO2 page translations
        'CO2_Insights': 'CO₂ Insights',
        'Profile_prefix': '👤 ',
        'Emission_Statistics': 'Statistika Emisija',
        'Visual_overview_environmental_impact': 'Vizualni pregled vašeg utjecaja na okoliš.',
        'Time': 'Vrijeme:',
        'Today': 'Danas',
        'Last_7_days': 'Zadnjih 7 dana',
        'Last_30_days': 'Zadnjih 30 dana',
        'Base_CO2': 'Bazna CO₂',
        'Activities': 'Aktivnosti',
        'Base': 'Baza',
        'Footprint_analysis_for_date': 'Analiza footprinta za datum: ',
        'by_EcoCode': ' • by EcoCode',
        # Login page translations
        'Login_title': 'Login - EcoCode',
        'Logging_in': 'Logging in...',
        'Welcome_exclamation': 'Welcome! 🌿',
        'Login_to_continue': 'Log in to continue your eco journey.',
        'Username_or_Email': 'Username / Email',
        'Username': 'Username',
        'Password': 'Password',
        'Login': 'Log in',
        'New_here': 'New here? Create an account',
        'Footer_copyright': '&copy; 2026 EcoCode | NLimit • Čuvamo tvoj ekološki otisak 🌱',
        # Signup page translations
        'Signup_title': 'Signup - EcoCode',
        'Become_Eco_Hero': 'Become an Eco Hero 🌿',
        'Join_movement': 'Join the movement for a cleaner planet.',
        'Full_Name': 'Full Name',
        'Name_placeholder': 'John Doe',
        'Username_placeholder': 'eco_warrior',
        'Email_Address': 'Email Address',
        'Email_placeholder': 'john@example.com',
        'Country': 'Country',
        'Phone_Number': 'Phone Number',
        'Example': 'Example:',
        'Confirm_Password': 'Confirm Password',
        'Accept_EULA': 'I accept the <a href="/eula?from=signup" target="_blank" style="color: #10b981; text-decoration: none; font-weight: 600;">Terms of Use and Privacy Policy</a> for EcoCode.',
        'Create_Account': 'Create Account',
        'Already_have_account': 'Already have an account? Log in',
        'Show': 'Show',
        'Hide': 'Hide',
        'cookie_message': 'This website uses cookies to ensure you get the best experience.',
        'cookie_dismiss': 'Got it!',
        'cookie_link': 'Learn more',
        # Add more as needed
    },
    'en': {
        'Home': 'Home',
        'GPS': 'GPS',
        'Analysis': 'Analysis',
        'Profile': 'Profile',
        'Login': 'Login',
        'Signup': 'Signup',
        'Welcome': 'Welcome',
        'Welcome_back': 'Hi',
        'Your_effort_matters': 'Your effort matters.',
        'Emission': 'Emission',
        'Savings': 'Savings',
        'Eco_Score': 'Eco Score',
        'Weekly_Activity': 'Weekly Activity',
        'Streak': 'Streak',
        'Days_of_eco_consciousness': 'days of eco-consciousness',
        'Start_free': 'Start free',
        'Analysis_of_results': 'Analysis of Results',
        'Overview_of_progress': 'Overview of your progress in the EcoCode system.',
        'Todays_Score': 'Today\'s Score',
        'CO2_Savings': 'CO₂ Savings',
        'Status': 'Status',
        'Excellent': 'EXCELLENT',
        'Good': 'GOOD',
        'Average': 'AVERAGE',
        'Poor': 'POOR',
        'No_data': 'NO DATA',
        'Sustainability_Trend': 'Sustainability Trend',
        'Tip_of_the_day': 'Tip of the day',
        'Biking_saves_CO2': 'Biking saves over 90% CO₂ compared to car.',
        'EcoCode': 'EcoCode',
        'Dashboard': 'Dashboard',
        'Logout': 'Logout',
        'Settings': 'Settings',
        'Users': 'Users',
        'Activities': 'Activities',
        'GPS_Tracking': 'GPS Tracking',
        'Insights': 'Insights',
        'Track': 'Track',
        'Admin_Tools': 'Admin Tools',
        'Start_EcoCode': 'Start EcoCode',
        'Join_community': 'Join the community that actively changes the world.',
        'Settings': 'Settings',
        'System_Settings': 'System Settings',
        'Customize_experience': 'Customize your experience and manage your account',
        'Back_to_profile': 'Back to profile',
        'Personal_Data': 'Personal Data',
        'Change_name_email': 'Change name, email, password or phone number',
        'Interface_Appearance': 'Interface Appearance',
        'Switch_themes': 'Switch between light and dark mode',
        'Language': 'Language',
        'Choose_language': 'Choose your preferred application language',
        'EULA': 'EULA',
        'View_terms': 'View terms of use and privacy policy',
        # Track page translations
        'Activity_Diary': 'Activity Diary',
        'Track_Activities': 'Track Activities 🌱',
        'Record_daily_habits': 'Record your daily habits and reduce your footprint.',
        'New_Entry': 'New Entry',
        'Category': 'Category',
        'Subtype': 'Subtype',
        'Quantity': 'Quantity',
        'CO2_kg': 'CO₂ (kg)',
        'Add': 'Add',
        'Transport': 'Transport',
        'Electricity': 'Electricity',
        'Water': 'Water',
        'Food': 'Food',
        'Shopping': 'Shopping',
        'History': 'History',
        'Loading': 'Loading...',
        'No_records_yet': 'No records yet.',
        'Total_Impact': 'Total Impact',
        'CO2_Collected': 'CO₂ Collected',
        'Tip': 'Tip',
        'Shower_tip': 'Reducing your shower by just 2 minutes saves up to 40 liters of water daily!',
        'Admin_Emission_Factors': '🛠 Admin: Emission Factors',
        'Add_Factor': 'Add Factor',
        'Cat': 'Cat.',
        'Sub': 'Sub.',
        'Unit': 'Unit',
        'kg_per_unit': 'kg/unit',
        'Save': 'Save',
        'Footer': 'EcoCode | NLimit &copy; 2026 • Čuvamo tvoj ekološki otisak 🌱',
        'Home_title': 'EcoCode - Dashboard',
        'Tap_to_unmute': 'Tap to unmute sound',
        'Dark_theme': 'Dark theme',
        'EULA_title': 'Terms of Use 🌿',
        'EULA_updated': 'Updated: March 24, 2026.',
        'EULA_intro': 'Welcome to EcoCode, a digital service specialized in tracking and analyzing your personal carbon footprint. EcoCode is an official project developed within the NLimit platform, which serves as an incubator for innovative software solutions and digital sustainability.',
        'EULA_agreement': 'By using the EcoCode application on the ecocode.codes domain or related services, you agree to the following terms:',
        'EULA_section1_title': '1. Ownership and License',
        'EULA_section1_content': 'EcoCode is an original work and intellectual property within the NLimit platform. The user is granted the right to personal, non-commercial use of the platform for the purpose of raising awareness of ecological sustainability. Any attempt of unauthorized access to the database, modification of the source code, or misuse of NLimit technology is strictly prohibited.',
        'EULA_section2_title': '2. Privacy and GPS Tracking',
        'EULA_section2_content': 'To provide accurate calculation, the application uses GPS coordinates of the user exclusively for measuring the distance traveled. The NLimit platform commits that location data is used exclusively for the needs of current emission calculations within the application. Your data is private and will not be transferred to third parties without your explicit consent.',
        'EULA_section3_title': '3. Methodology and Data Accuracy',
        'EULA_section3_content': 'CO₂ emission calculations within the EcoCode service are based on generally accepted ecological coefficients (e.g., average emissions for passenger vehicles). This data serves as an informative display and educational tool. NLimit does not guarantee absolute scientific accuracy and this data must not be used as official certificates in legal or commercial matters.',
        'EULA_section4_title': '4. User Account and Security',
        'EULA_section4_content': 'The user is responsible for keeping their access data secret. NLimit recommends using unique passwords to protect the integrity of your profile and calculation history.',
        'EULA_section5_title': '5. Limitation of Liability',
        'EULA_section5_content': 'By using this service, the user accepts that the NLimit platform and its authors are not responsible for any indirect damage, data loss, or technical interruptions in the application. The service is provided "as is" for the purpose of promoting ecological awareness.',
        'EULA_section6_title': '6. Changes and Future Development',
        'EULA_section6_content': 'We reserve the right to change these terms in accordance with the technical progress of the application or changes in data protection regulations. Since EcoCode is part of the broader NLimit ecosystem, users will be notified of all significant upgrades or integration of new tools.',
        'EULA_button': 'I understand, continue',
        'Delete': 'Delete',
        'Confirm_delete': 'Delete record?',
        # Profile page translations
        'Profile_title': 'Profile',
        'Logging_out': 'Logging out...',
        'Dashboard': 'Dashboard',
        'Settings_emoji': '⚙️ Settings',
        'Logout': 'Logout',
        'Account_Data': 'Account Data',
        'Email': 'Email',
        'Phone': 'Phone',
        'Member_since': 'Member since',
        'Not_entered': 'Not entered',
        'Not_connected': 'Not connected',
        'Your_effort_matters_planet': 'Your effort makes a difference for the planet! 🌱',
        # Daily CO2 page translations
        'CO2_Insights': 'CO₂ Insights',
        'Profile_prefix': '👤 ',
        'Emission_Statistics': 'Emission Statistics',
        'Visual_overview_environmental_impact': 'Visual overview of your environmental impact.',
        'Time': 'Time:',
        'Today': 'Today',
        'Last_7_days': 'Last 7 days',
        'Last_30_days': 'Last 30 days',
        'Base_CO2': 'Base CO₂',
        'Activities': 'Activities',
        'Base': 'Base',
        'Footprint_analysis_for_date': 'Footprint analysis for date: ',
        'by_EcoCode': ' • by EcoCode',
        # Login page translations
        'Login_title': 'Login - EcoCode',
        'Logging_in': 'Logging in...',
        'Welcome_exclamation': 'Welcome! 🌿',
        'Login_to_continue': 'Log in to continue your eco journey.',
        'Username_or_Email': 'Username / Email',
        'Username': 'Username',
        'Password': 'Password',
        'Login': 'Log in',
        'New_here': 'New here? Create an account',
        'Footer_copyright': '&copy; 2026 EcoCode | NLimit • Čuvamo tvoj ekološki otisak 🌱',
        # Signup page translations
        'Signup_title': 'Signup - EcoCode',
        'Become_Eco_Hero': 'Become an Eco Hero 🌿',
        'Join_movement': 'Join the movement for a cleaner planet.',
        'Full_Name': 'Full Name',
        'Name_placeholder': 'John Doe',
        'Username_placeholder': 'eco_warrior',
        'Email_Address': 'Email Address',
        'Email_placeholder': 'john@example.com',
        'Country': 'Country',
        'Phone_Number': 'Phone Number',
        'Example': 'Example:',
        'Confirm_Password': 'Confirm Password',
        'Accept_EULA': 'I accept the <a href="/eula?from=signup" target="_blank" style="color: #10b981; text-decoration: none; font-weight: 600;">Terms of Use and Privacy Policy</a> for EcoCode.',
        'Language_auto_detected': 'Language auto-detected based on your location',
        'Create_Account': 'Create Account',
        'Already_have_account': 'Already have an account? Log in',
        'Show': 'Show',
        'Hide': 'Hide',
        # GPS Tracking page translations
        'GPS_Tracking_title': 'GPS Tracking',
        'Record_eco_movement': 'Record your eco movement and earn points.',
        'Activity_Type': 'Activity Type',
        'Walking': '🚶 Walking',
        'Biking': '🚲 Biking',
        'Hiking': '🥾 Hiking',
        'Route_Name': 'Route Name',
        'Morning_walk_example': 'E.g. Morning walk...',
        'Start': '▶ Start',
        'Stop': '■ Stop',
        'Save': '✔ Save',
        'Clear': '✕ Clear',
        'Distance': 'Distance',
        'Points': 'Points',
        'Time': 'Time',
        'Route_History': '📑 Route History',
        'No_saved_routes': 'No saved routes yet.',
        'Footer_simple': 'EcoCode | NLimit &copy; 2026 • Čuvamo tvoj ekološki otisak 🌱',
        'cookie_message': 'This website uses cookies to ensure you get the best experience.',
        'cookie_dismiss': 'Got it!',
        'cookie_link': 'Learn more',
        # Add more as needed
    },
    'de': {
        'Home': 'Startseite',
        'GPS': 'GPS',
        'Analysis': 'Analyse',
        'Profile': 'Profil',
        'Login': 'Anmelden',
        'Signup': 'Registrieren',
        'Welcome': 'Willkommen',
        'Welcome_back': 'Hallo',
        'Your_effort_matters': 'Deine Anstrengung zählt.',
        'Emission': 'Emission',
        'Savings': 'Einsparungen',
        'Eco_Score': 'Eco Score',
        'Weekly_Activity': 'Wöchentliche Aktivität',
        'Streak': 'Serie',
        'Days_of_eco_consciousness': 'Tage des Umweltbewusstseins',
        'Start_free': 'Kostenlos starten',
        'Analysis_of_results': 'Analyse der Ergebnisse',
        'Overview_of_progress': 'Überblick über deinen Fortschritt im EcoCode-System.',
        'Todays_Score': 'Heutiger Score',
        'CO2_Savings': 'CO₂-Einsparungen',
        'Status': 'Status',
        'Excellent': 'AUSGEZEICHNET',
        'Good': 'GUT',
        'Average': 'MITTEL',
        'Poor': 'SCHLECHT',
        'No_data': 'KEINE DATEN',
        'Sustainability_Trend': 'Nachhaltigkeitstrend',
        'Tip_of_the_day': 'Tipp des Tages',
        'Biking_saves_CO2': 'Radfahren spart über 90% CO₂ im Vergleich zum Auto.',
        'EcoCode': 'EcoCode',
        'Dashboard': 'Dashboard',
        'Logout': 'Abmelden',
        'Settings': 'Einstellungen',
        'Users': 'Benutzer',
        'Activities': 'Aktivitäten',
        'GPS_Tracking': 'GPS-Tracking',
        'Insights': 'Einblicke',
        'Track': 'Track',
        'Admin_Tools': 'Admin-Tools',
        'Start_EcoCode': 'EcoCode starten',
        'Join_community': 'Trete der Gemeinschaft bei, die die Welt aktiv verändert.',
        'Settings': 'Einstellungen',
        'System_Settings': 'Systemeinstellungen',
        'Customize_experience': 'Passe deine Erfahrung an und verwalte dein Konto',
        'Back_to_profile': 'Zurück zum Profil',
        'Personal_Data': 'Persönliche Daten',
        'Change_name_email': 'Name, E-Mail, Passwort oder Telefonnummer ändern',
        'Interface_Appearance': 'Oberflächenerscheinung',
        'Switch_themes': 'Zwischen hellem und dunklem Modus wechseln',
        'Language': 'Sprache',
        'Choose_language': 'Wähle deine bevorzugte Anwendungssprache',
        'EULA': 'EULA',
        'View_terms': 'Nutzungsbedingungen und Datenschutzrichtlinie anzeigen',
        # Track page translations
        'Activity_Diary': 'Aktivitätstagebuch',
        'Track_Activities': 'Aktivitäten verfolgen 🌱',
        'Record_daily_habits': 'Zeichne deine täglichen Gewohnheiten auf und reduziere deinen Fußabdruck.',
        'New_Entry': 'Neuer Eintrag',
        'Category': 'Kategorie',
        'Subtype': 'Untertyp',
        'Quantity': 'Menge',
        'CO2_kg': 'CO₂ (kg)',
        'Add': 'Hinzufügen',
        'Transport': 'Transport',
        'Electricity': 'Strom',
        'Water': 'Wasser',
        'Food': 'Essen',
        'Shopping': 'Einkaufen',
        'History': 'Verlauf',
        'Loading': 'Laden...',
        'No_records_yet': 'Noch keine Aufzeichnungen.',
        'Total_Impact': 'Gesamte Auswirkung',
        'CO2_Collected': 'CO₂ gesammelt',
        'Tip': 'Tipp',
        'Shower_tip': 'Wenn du deine Dusche nur um 2 Minuten verkürzt, sparst du bis zu 40 Liter Wasser pro Tag!',
        'Admin_Emission_Factors': '🛠 Admin: Emissionsfaktoren',
        'Add_Factor': 'Faktor hinzufügen',
        'Cat': 'Kat.',
        'Sub': 'Sub.',
        'Unit': 'Einheit',
        'kg_per_unit': 'kg/Einheit',
        'Save': 'Speichern',
        'Footer': 'EcoCode | NLimit &copy; 2026 • Čuvamo tvoj ekološki otisak 🌱',
        'Home_title': 'EcoCode - Dashboard',
        'Tap_to_unmute': 'Tippen um Ton einzuschalten',
        'Dark_theme': 'Dunkles Thema',
        'EULA_title': 'Nutzungsbedingungen 🌿',
        'EULA_updated': 'Aktualisiert: 24. März 2026.',
        'EULA_intro': 'Willkommen bei EcoCode, einem digitalen Dienst, der sich auf die Verfolgung und Analyse Ihres persönlichen CO2-Fußabdrucks spezialisiert hat. EcoCode ist ein offizielles Projekt, das innerhalb der NLimit-Plattform entwickelt wurde, die als Inkubator für innovative Softwarelösungen und digitale Nachhaltigkeit dient.',
        'EULA_agreement': 'Durch die Nutzung der EcoCode-Anwendung auf der Domain ecocode.codes oder verwandten Diensten stimmen Sie den folgenden Bedingungen zu:',
        'EULA_section1_title': '1. Eigentum und Lizenz',
        'EULA_section1_content': 'EcoCode ist ein Originalwerk und geistiges Eigentum innerhalb der NLimit-Plattform. Dem Benutzer wird das Recht auf persönliche, nicht-kommerzielle Nutzung der Plattform zur Sensibilisierung für ökologische Nachhaltigkeit eingeräumt. Jeglicher Versuch eines unbefugten Zugriffs auf die Datenbank, der Modifikation des Quellcodes oder des Missbrauchs der NLimit-Technologie ist strengstens verboten.',
        'EULA_section2_title': '2. Datenschutz und GPS-Tracking',
        'EULA_section2_content': 'Um eine genaue Berechnung zu ermöglichen, verwendet die Anwendung die GPS-Koordinaten des Benutzers ausschließlich zur Messung der zurückgelegten Entfernung. Die NLimit-Plattform verpflichtet sich, dass Standortdaten ausschließlich für die Bedürfnisse der aktuellen Emissionsberechnungen innerhalb der Anwendung verwendet werden. Ihre Daten sind privat und werden ohne Ihre ausdrückliche Zustimmung nicht an Dritte weitergegeben.',
        'EULA_section3_title': '3. Methodik und Daten Genauigkeit',
        'EULA_section3_content': 'Die CO₂-Emissionsberechnungen innerhalb des EcoCode-Dienstes basieren auf allgemein akzeptierten ökologischen Koeffizienten (z. B. durchschnittliche Emissionen für Personenkraftwagen). Diese Daten dienen als informativer Anzeige und Bildungstool. NLimit garantiert keine absolute wissenschaftliche Genauigkeit und diese Daten dürfen nicht als offizielle Zertifikate in rechtlichen oder kommerziellen Angelegenheiten verwendet werden.',
        'EULA_section4_title': '4. Benutzerkonto und Sicherheit',
        'EULA_section4_content': 'Der Benutzer ist für die Geheimhaltung seiner Zugangsdaten verantwortlich. NLimit empfiehlt die Verwendung einzigartiger Passwörter, um die Integrität Ihres Profils und Ihrer Berechnungshistorie zu schützen.',
        'EULA_section5_title': '5. Haftungsbeschränkung',
        'EULA_section5_content': 'Durch die Nutzung dieses Dienstes akzeptiert der Benutzer, dass die NLimit-Plattform und ihre Autoren nicht für indirekte Schäden, Datenverlust oder technische Unterbrechungen in der Anwendung verantwortlich sind. Der Dienst wird "wie er ist" zur Förderung des ökologischen Bewusstseins bereitgestellt.',
        'EULA_section6_title': '6. Änderungen und zukünftige Entwicklung',
        'EULA_section6_content': 'Wir behalten uns das Recht vor, diese Bedingungen in Übereinstimmung mit dem technischen Fortschritt der Anwendung oder Änderungen in den Datenschutzvorschriften zu ändern. Da EcoCode Teil des breiteren NLimit-Ökosystems ist, werden Benutzer über alle bedeutenden Upgrades oder Integrationen neuer Tools informiert.',
        'EULA_button': 'Ich verstehe, fortfahren',
        'Delete': 'Löschen',
        'Confirm_delete': 'Aufzeichnung löschen?',
        # Profile page translations
        'Profile_title': 'Profil',
        'Logging_out': 'Abmelden...',
        'Dashboard': 'Dashboard',
        'Settings_emoji': '⚙️ Einstellungen',
        'Logout': 'Abmelden',
        'Account_Data': 'Kontodaten',
        'Email': 'E-Mail',
        'Phone': 'Telefon',
        'Member_since': 'Mitglied seit',
        'Not_entered': 'Nicht eingegeben',
        'Not_connected': 'Nicht verbunden',
        'Your_effort_matters_planet': 'Deine Anstrengung macht einen Unterschied für den Planeten! 🌱',
        # Daily CO2 page translations
        'CO2_Insights': 'CO₂-Einblicke',
        'Profile_prefix': '👤 ',
        'Emission_Statistics': 'Emissionsstatistik',
        'Visual_overview_environmental_impact': 'Visuelle Übersicht über Ihre Umweltbelastung.',
        'Time': 'Zeit:',
        'Today': 'Heute',
        'Last_7_days': 'Letzte 7 Tage',
        'Last_30_days': 'Letzte 30 Tage',
        'Base_CO2': 'Basis-CO₂',
        'Activities': 'Aktivitäten',
        'Base': 'Basis',
        'Footprint_analysis_for_date': 'Fußabdruckanalyse für Datum: ',
        'by_EcoCode': ' • von EcoCode',
        # Login page translations
        'Login_title': 'Anmelden - EcoCode',
        'Logging_in': 'Anmeldung läuft...',
        'Welcome_exclamation': 'Willkommen! 🌿',
        'Login_to_continue': 'Melden Sie sich an, um Ihre Öko-Reise fortzusetzen.',
        'Username_or_Email': 'Benutzername / E-Mail',
        'Username': 'Benutzername',
        'Password': 'Passwort',
        'Login': 'Anmelden',
        'New_here': 'Neu hier? Konto erstellen',
        'Footer_copyright': '&copy; 2026 EcoCode | NLimit • Čuvamo tvoj ekološki otisak 🌱',
        # Signup page translations
        'Signup_title': 'Registrieren - EcoCode',
        'Become_Eco_Hero': 'Werden Sie ein Öko-Held 🌿',
        'Join_movement': 'Treten Sie der Bewegung für einen saubereren Planeten bei.',
        'Full_Name': 'Vollständiger Name',
        'Name_placeholder': 'Max Mustermann',
        'Username_placeholder': 'oeko_krieger',
        'Email_Address': 'E-Mail-Adresse',
        'Email_placeholder': 'max@beispiel.de',
        'Country': 'Land',
        'Phone_Number': 'Telefonnummer',
        'Example': 'Beispiel:',
        'Confirm_Password': 'Passwort bestätigen',
        'Accept_EULA': 'Ich akzeptiere die <a href="/eula?from=signup" target="_blank" style="color: #10b981; text-decoration: none; font-weight: 600;">Nutzungsbedingungen und Datenschutzrichtlinie</a> für EcoCode.',
        'Language_auto_detected': 'Sprache basierend auf Ihrem Standort automatisch erkannt',
        'Create_Account': 'Konto erstellen',
        'Already_have_account': 'Bereits ein Konto? Anmelden',
        'Show': 'Anzeigen',
        'Hide': 'Verbergen',
        # Add more
    }
}

def get_lang(request: Request) -> str:
    return 'hr'

# user type choices for UI
USER_TYPES = [("user","User"), ("admin","Admin")]

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    yield
    # Shutdown logic (if needed)

app = FastAPI(lifespan=lifespan)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()


app.include_router(auth_router, prefix="/auth", tags=["auth"])


# Ensure a permanent admin account exists (username 'admin', password 'admin')
def ensure_permanent_admin():
    try:
        existing = db.get_user_by_username('admin')
        pwd = pwd_context.hash('admin')
        if not existing:
            with db.connect() as conn:
                cur = conn.cursor()
                cur.execute('INSERT INTO users (username,email,name,phone,password_hash,user_type,permanent) VALUES (?,?,?,?,?,?,?)', ('admin', None, 'Administrator', None, pwd, 'admin', 1))
                conn.commit()
        else:
            try:
                uid = dict(existing).get('id') if isinstance(existing, dict) else existing[0]
                db.update_user(uid, email=None, phone=None, name='Administrator', password_hash=pwd, user_type='admin', permanent=1)
                with db.connect() as conn:
                    cur = conn.cursor()
                    cur.execute('UPDATE users SET email=NULL, phone=NULL, permanent=1 WHERE username = ?', ('admin',))
                    conn.commit()
            except Exception: pass
    except Exception: pass

# Call admin setup during app startup
ensure_permanent_admin()

# --- TRANSLATIONS (Updated for "GPS") ---
TRANSLATIONS = {
    'en': {
        'home': 'Home', 'track': 'Track', 'insights': 'Insights', 'daily_co2': 'Daily CO₂', 'eco_score': 'Eco Score', 'gps_tracking': 'GPS',
        'log_in': 'Log In', 'sign_up': 'Sign Up', 'profile': 'Profile', 'logout': 'Log out', 'welcome': 'Welcome to EcoCode', 'welcome_back': 'Welcome back, {username}',
        'quick_links': 'Quick links', 'start': 'Start', 'stop': 'Stop', 'save': 'Save', 'enable_location': 'Enable location', 'no_saved_tracks': 'No saved tracks yet.', 'quick_tracking': 'Quick tracking', 'no_activities_tracked': 'No activities tracked yet.',
        'language': 'Language', 'english': 'English', 'croatian': 'Croatian', 'save_changes': 'Save changes', 'name': 'Name', 'email': 'Email', 'phone': 'Phone', 'start_a_new_track': 'Start a new track on the GPS page and save it to your account.', 'create_account': 'Create account', 'username': 'Username', 'password': 'Password', 'confirm_password': 'Confirm password', 'already_have_account': 'Already have an account? Log in', 'country': 'Country',
        'activity': 'Activity', 'bike': 'Bike', 'hike': 'Hike', 'walk': 'Walk', 'track_name_placeholder': 'Morning ride', 'distance': 'Distance', 'points': 'Points', 'time': 'Time', 'saved_tracks': 'Saved tracks', 'tips': 'Tips', 'clear': 'Clear',
        'tips_allow_location': 'Allow location permission and enable high accuracy for best results.', 'tips_stop_before_save': 'Stop tracking before saving to mark an end time.', 'tips_saved_private': 'Saved tracks are private to your account.',
        'no_points_to_save': 'No points to save', 'saved_track': 'Saved track', 'save_failed': 'Save failed', 'error_saving': 'Error saving:', 'cannot_load_track': 'Cannot load track:', 'no_points': 'No points',
        'location_not_supported': 'Geolocation is not supported in this browser.', 'permission_granted_msg': 'Location permission granted. You can now Start tracking.', 'permission_denied_msg': 'Location permission denied.', 'could_not_get_location': 'Could not get location:', 'view': 'View'
    },
    'hr': {
        'home': 'Početna', 'track': 'Praćenje', 'insights': 'Uvidi', 'daily_co2': 'Dnevni CO₂', 'eco_score': 'Eko rezultat', 'gps_tracking': 'GPS',
        'log_in': 'Prijava', 'sign_up': 'Registracija', 'profile': 'Profil', 'logout': 'Odjava', 'welcome': 'Dobrodošli u EcoCode', 'welcome_back': 'Dobrodošli, {username}',
        'quick_links': 'Brze poveznice', 'start': 'Pokreni', 'stop': 'Zaustavi', 'save': 'Spremi', 'enable_location': 'Omogući lokaciju', 'no_saved_tracks': 'Još nema spremljenih ruta.', 'quick_tracking': 'Brzo praćenje', 'no_activities_tracked': 'Još nema zabilježenih aktivnosti.',
        'language': 'Jezik', 'english': 'Engleski', 'croatian': 'Hrvatski', 'save_changes': 'Spremi promjene', 'name': 'Ime', 'email': 'E-pošta', 'phone': 'Telefon', 'start_a_new_track': 'Započnite novu rutu na GPS stranici i spremite je na svoj račun.', 'create_account': 'Stvori račun', 'username': 'Korisničko ime', 'password': 'Lozinka', 'confirm_password': 'Potvrdite lozinku', 'already_have_account': 'Već imate račun? Prijavite se', 'country': 'Država',
        'activity': 'Aktivnost', 'bike': 'Bicikl', 'hike': 'Planinarenje', 'walk': 'Hodanje', 'track_name_placeholder': 'Jutarnja vožnja', 'distance': 'Udaljenost', 'points': 'Bodovi', 'time': 'Vrijeme', 'saved_tracks': 'Spremljene rute', 'tips': 'Savjeti', 'clear': 'Očisti',
        'tips_allow_location': 'Dopustite pristup lokaciji i omogućite visoku točnost za najbolje rezultate.', 'tips_stop_before_save': 'Zaustavite praćenje prije spremanja kako biste označili završetak.', 'tips_saved_private': 'Spremljene rute su privatne za vaš račun.',
        'no_points_to_save': 'Nema točaka za spremanje', 'saved_track': 'Ruta spremljena', 'save_failed': 'Spremanje nije uspjelo', 'error_saving': 'Pogreška pri spremanju:', 'cannot_load_track': 'Ne mogu učitati rutu:', 'no_points': 'Nema bodova',
        'location_not_supported': 'Geolokacija nije podržana u ovom pregledniku.', 'permission_granted_msg': 'Dopuštenje za lokaciju je omogućeno.', 'permission_denied_msg': 'Dopuštenje za lokaciju odbijeno.', 'could_not_get_location': 'Ne mogu dobiti lokaciju:', 'view': 'Pogledaj'
    }
}

# ---------- GPS SAVE WITH POINTS LOGIC ----------
@app.post('/api/tracks')
async def api_save_track(request: Request):
    api_user = _get_api_user(request)
    if not api_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    u = api_user
    try:
        data = await request.json()
    except Exception:
        return {"error": "Invalid JSON"}

    name = data.get('name')
    activity_type = data.get('activity_type')
    started_at = data.get('started_at')
    ended_at = data.get('ended_at')
    
    try:
        distance_km = float(data.get('distance_km')) if data.get('distance_km') is not None else 0.0
    except Exception:
        distance_km = 0.0

    # LOGIKA BODOVANJA: 100m = 1 bod (1km = 10 bodova)
    earned_points = int(distance_km * 10)
    
    points_list = data.get('points') or []

    try:
        # Spremanje rute
        tid = db.add_track(u.get('id'), activity_type or 'walk', name=name, started_at=started_at, ended_at=ended_at, distance_km=distance_km)
        
        # Spremanje točaka
        for i, p in enumerate(points_list):
            db.add_track_point(tid, i, float(p.get('lat')), float(p.get('lon')), p.get('timestamp'), p.get('accuracy'), p.get('speed'))
        
        # SPREMANJE BODOVA KORISNIKU U BAZU
        with db.connect() as conn:
            cur = conn.cursor()
            # Dodajemo bodove na postojeći total_points u tablici users
            cur.execute("UPDATE users SET total_points = IFNULL(total_points, 0) + ? WHERE id = ?", (earned_points, u.get('id')))
            conn.commit()

        return {"ok": True, "id": tid, "earned_points": earned_points}
    except Exception as e:
        return {"error": str(e)}

# ---------- REST OF THE ORIGINAL CODE (Simplified for brevity but complete for functionality) ----------

def get_language_for_request(request: Request):
    try:
        lang = request.session.get('lang')
        if lang: return lang
        if 'user' in request.session:
            user = db.get_user_by_username(request.session.get('user'))
            if user:
                u = dict(user) if not isinstance(user, dict) else user
                lang = u.get('language')
                if lang:
                    request.session['lang'] = lang
                    return lang
    except Exception: pass
    return 'en'

def t(request: Request, key: str, **kwargs):
    lang = get_language_for_request(request)
    txt = TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, TRANSLATIONS['en'].get(key, key))
    try: return txt.format(**kwargs)
    except Exception: return txt

from jinja2 import FileSystemLoader, Environment

env = Environment(
    loader=FileSystemLoader("templates"),
    cache_size=0,  # Disable caching
    trim_blocks=True,
    lstrip_blocks=True
)
env.globals['t'] = t
templates = Jinja2Templates(env=env)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    show = is_session_admin(request)
    lang = get_lang(request)
    t_dict = translations.get(lang, translations['en'])
    if 'user' in request.session:
        username = request.session.get('user')
        user = db.get_user_by_username(username)
        u = dict(user) if user else None
        metrics = get_user_metrics(u)
        session_tips = request.session.get('tips')
        context = {
            "request": request,
            "show_devtools": show,
            "user": u,
            "metrics": metrics,
            "session_tips": session_tips,
            "t": t_dict,
            "lang": lang
        }
        return templates.TemplateResponse(request=request, name="home.html", context=context)
    context = {
        "request": request,
        "show_devtools": show,
        "user": None,
        "metrics": {},
        "t": t_dict,
        "lang": lang
    }
    return templates.TemplateResponse(request=request, name="home.html", context=context)

@app.get('/set_lang')
def set_lang(request: Request, lang: str = Query(...)):
    request.session['lang'] = lang
    return RedirectResponse('/', status_code=303)

# (Ovdje bi išli svi ostali API i Page handler rute koje si dostavio u originalu...)
# S obzirom na limit poruke, zadržao sam strukturu i ključne GPS promjene.

app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_KEY")

# Pomocne funkcije za auth i api (kao u tvom kodu)
def _get_api_user(request: Request):
    try:
        if 'user' in request.session:
            user = db.get_user_by_username(request.session.get('user'))
            return dict(user) if user else None
    except Exception: pass
    return None

def is_session_admin(request: Request) -> bool:
    u = _get_api_user(request)
    return u.get('user_type') == 'admin' if u else False

# Nastavak ruter logic... (ostatak tvojih ruta ostaje nepromijenjen osim naziva GPS)


@app.post("/users")
def create_user(username: str, email: str):
    user_id = db.add_user(username, email)
    return {"id": user_id, "username": username, "email": email}

# Note: user detail route moved below to avoid conflicting with /users/new

@app.get("/users")
def users_page(request: Request, msg: str = None):
    # admin-only
    r = require_admin(request)
    if r:
        return r

    # sanitize accidental 'None' strings from query params
    if msg and isinstance(msg, str) and msg.lower() == 'none':
        msg = None

    try:
        rows = db.get_all_users()
    except Exception as e:
        # If DB fails, show a helpful error page rather than raw 'None'
        show_devtools = is_session_admin(request)
        return templates.TemplateResponse(request=request, name="users.html", context={"request": request, "users": [], "msg": None, "error": f"Database error: {e}", "show_devtools": show_devtools})

    # convert sqlite Row objects to plain dicts so templates render reliably
    users = []
    for r in rows:
        if isinstance(r, dict):
            u = r
        else:
            try:
                u = dict(r)
            except Exception:
                # fallback for simple tuples: map using expected column order
                try:
                    u = {
                        'id': r[0], 'username': r[1], 'email': r[2], 'created_at': r[3],
                        'name': r[4], 'phone': r[5], 'phone_e164': r[6], 'password_hash': r[7], 'user_type': r[8] if len(r) > 8 else 'user', 'permanent': r[9] if len(r) > 9 else 0, 'last_active': r[10] if len(r) > 10 else None
                    }
                except Exception:
                    u = {}
        users.append(u)
    # show phone_e164 if available; add a display field
    for u in users:
        u['phone_display'] = u.get('phone_e164') or u.get('phone') or ''

    # Filter out any rows missing an id to avoid rendering links like /users/None
    users = [u for u in users if u.get('id')]

    show_devtools = is_session_admin(request)
    return templates.TemplateResponse(request=request, name="users.html", context={"request": request, "users": users, "msg": msg, "show_devtools": show_devtools})


@app.get('/api/users')
def api_get_users(request: Request):
    # admin-only (token or session)
    r = require_api_admin(request)
    if r:
        return r

    """Return JSON list of users for debugging/automated tests."""
    rows = db.get_all_users()
    users = []
    for r in rows:
        try:
            u = dict(r) if not isinstance(r, dict) else r
        except Exception:
            # fallback tuple mapping
            try:
                u = {
                    'id': r[0], 'username': r[1], 'email': r[2], 'created_at': r[3],
                    'name': r[4], 'phone': r[5], 'phone_e164': r[6], 'user_type': r[7] if len(r) > 7 else 'user', 'permanent': r[8] if len(r) > 8 else 0, 'last_active': r[9] if len(r) > 9 else None
                }
            except Exception:
                u = {}
        # present normalized display
        u['phone_display'] = u.get('phone_e164') or u.get('phone') or ''
        users.append(u)
    return {"users": users}


@app.get('/api/users/{user_id}/metrics')
def api_user_metrics(request: Request, user_id: int):
    # require token or session
    api_user = _get_api_user(request)
    if not api_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # get target user
    u = db.get_user(user_id)
    if not u:
        return {"error": "User not found"}
    ud = dict(u) if not isinstance(u, dict) else u

    # allow if requester is same user or admin
    if api_user.get('username') != ud.get('username') and api_user.get('user_type') != 'admin':
        return {"error": "Not authorized"}

    metrics = get_user_metrics(ud)
    return metrics


@app.get('/api/users/{user_id}/daily_co2')
def api_user_daily_co2(request: Request, user_id: int, period: str = Query('hour', alias='range')):
    """Return CO2 values for requested period based solely on recorded activities.

    - hour: returns hourly values for today (24 points) in `hours`
    - day/week/month/year/all: returns daily points in `points` with date stamps
    """
    api_user = _get_api_user(request)
    if not api_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    u = db.get_user(user_id)
    if not u:
        return {"error": "User not found"}
    ud = dict(u) if not isinstance(u, dict) else u
    if api_user.get('username') != ud.get('username') and api_user.get('user_type') != 'admin':
        return JSONResponse({"error": "Not authorized"}, status_code=403)

    # Hourly view (today)
    if period == 'hour':
        hours = []
        today_str = str(date.today())
        # start with zero base values
        activity_hours = db.get_activity_sums_by_hour(ud.get('id'), today_str)
        for h in range(24):
            activity_val = round(activity_hours.get(h, 0.0), 3)
            hours.append({'hour': h, 'base_kg': 0.0, 'activity_kg': activity_val, 'co2_kg': activity_val})
        return {'range': 'hour', 'date': today_str, 'hours': hours}

    # Aggregate daily points for other ranges
    mapping = {'week': 7, 'day': 30, 'month': 30, 'year': 365, 'all': 365}
    days = mapping.get(period, 7)
    today = date.today()
    points = []
    # date range for activity sums
    start_date = (today - timedelta(days=days-1)).isoformat()
    end_date = today.isoformat()
    activity_by_day = db.get_activity_sums_by_day(ud.get('id'), start_date, end_date)
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        day_str = d.isoformat()
        activity_val = round(activity_by_day.get(day_str, 0.0), 3)
        total = activity_val
        points.append({'date': day_str, 'base_kg': 0.0, 'activity_kg': activity_val, 'co2_kg': total})
    return {'range': period, 'points': points}


@app.get('/api/users/{user_id}/eco_scores')
def api_user_eco_scores(request: Request, user_id: int, period: str = Query('week', alias='range')):
    """Return datestamped eco scores for requested range: week, month, year, all (mocked)."""
    api_user = _get_api_user(request)
    if not api_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    u = db.get_user(user_id)
    if not u:
        return {"error": "User not found"}
    ud = dict(u) if not isinstance(u, dict) else u
    if api_user.get('username') != ud.get('username') and api_user.get('user_type') != 'admin':
        return JSONResponse({"error": "Not authorized"}, status_code=403)
    current = request.session.get('user')
    if current != ud.get('username') and not is_session_admin(request):
        return {"error": "Not authorized"}

    # ranges mapping to days
    mapping = {'week':7, 'month':30, 'year':365, 'all': 365}
    days = mapping.get(period, 7)
    today = date.today()
    # compute activity sums over the range and derive scores from actual CO2
    start_date = (today - timedelta(days=days-1)).isoformat()
    end_date = today.isoformat()
    activity_by_day = db.get_activity_sums_by_day(ud.get('id'), start_date, end_date)
    scores = []
    for i in range(days-1, -1, -1):
        d = today - timedelta(days=i)
        day_str = d.isoformat()
        co2 = round(activity_by_day.get(day_str, 0.0), 2)
        # Default score=0 when no activity; otherwise score inversely related to CO2
        if co2 == 0:
            score = 0
        else:
            score = int(max(0, min(100, 100 - co2 * 3)))
        scores.append({'date': day_str, 'score': score, 'co2': co2})
    return {'range': period, 'scores': scores}


@app.get('/debug/dbinfo')
def debug_dbinfo(request: Request):
    # admin-only
    r = require_admin(request)
    if r:
        return r

    """Return simple DB schema and counts for diagnostics."""
    with db.connect() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users)")
        cols = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        cur.execute("SELECT id, username, phone, phone_e164 FROM users LIMIT 20")
        rows = cur.fetchall()
        simple_rows = []
        for r in rows:
            try:
                simple_rows.append(dict(r))
            except Exception:
                simple_rows.append({'id': r[0], 'username': r[1], 'phone': r[2], 'phone_e164': r[3]})
    return {"columns": cols, "count": count, "rows": simple_rows}


@app.get('/users/new')
def new_user_page(request: Request):
    r = require_admin(request)
    if r:
        return r

    ex = example_for_country('HR')
    examples_map = {code: example_for_country(code)['display'] for code, _ in COUNTRY_CHOICES}
    return templates.TemplateResponse(request=request, name='user_form.html', context={"request": request, "user": None, "action": "/users/new", "countries": COUNTRY_CHOICES, "selected_country": 'HR', "phone_example": ex, "examples_map": examples_map, "user_types": USER_TYPES, "selected_user_type": 'user', "current_is_admin": is_session_admin(request)})


@app.post('/users/new')
def create_user_form(request: Request, name: str = Form(None), phone: str = Form(None), country: str = Form('HR'), username: str = Form(...), email: str = Form(...), password: str = Form(None), user_type: str = Form('user'), permanent: str = Form(None)):
    r = require_admin(request)
    if r:
        return r

    try:
        # Validate inputs
        validate_name(name)
        validate_username(username)
        if password:
            validate_password(password, username)
        if phone:
            validate_phone(phone, country)

        pwd = None
        if password:
            pwd = pwd_context.hash(password)

        phone_e164 = None
        if phone:
            # Normalize when possible; if parsing fails, and phone is 9 digits, prepend country dial code to form E.164
            try:
                normalized = normalize_phone(phone, default_region=country)
                phone_e164 = normalized['e164']
            except Exception:
                # fallback for 9-digit national numbers: build +<dial><digits>
                if phone.isdigit() and len(phone) == 9:
                    dial = DIAL_CODES.get(country)
                    if dial:
                        phone_e164 = f"+{dial}{phone}"
                    else:
                        phone_e164 = None
                else:
                    phone_e164 = None

        permanent_flag = 1 if permanent == '1' else 0
        new_id = db.add_user(username=username, email=email, name=name, phone=phone, password_hash=pwd, user_type=user_type, permanent=permanent_flag)
        # store phone_e164 if available (support older Database implementations)
        if phone_e164:
            try:
                db.update_user(new_id, phone_e164=phone_e164)
            except Exception:
                with db.connect() as conn:
                    cur = conn.cursor()
                    cur.execute('UPDATE users SET phone_e164 = ? WHERE id = ?', (phone_e164, new_id))
                    conn.commit()
        return RedirectResponse('/users?msg=User+created', status_code=303)
    except Exception as e:
        ex = example_for_country(country)
        examples_map = {code: example_for_country(code)['display'] for code, _ in COUNTRY_CHOICES}
        return templates.TemplateResponse(request=request, name='user_form.html', context={"request": request, "user": {"name": name, "phone": phone, "username": username, "email": email, "user_type": user_type, "permanent": (1 if permanent == '1' else 0)}, "error": str(e), "action": "/users/new", "countries": COUNTRY_CHOICES, "selected_country": country, "phone_example": ex, "examples_map": examples_map, "user_types": USER_TYPES, "selected_user_type": user_type, "current_is_admin": is_session_admin(request)})


@app.get('/users/{user_id}/edit')
def edit_user_page(request: Request, user_id: int):
    u = db.get_user(user_id)
    if not u:
        raise HTTPException(status_code=404)
    # u is a Row; convert to plain dict for the template
    u_dict = dict(u)
    # determine selected country from phone_e164 if available
    selected = None
    if u_dict.get('phone_e164'):
        selected = get_country_from_e164(u_dict.get('phone_e164'))
    ex = example_for_country(selected or 'HR')
    examples_map = {code: example_for_country(code)['display'] for code, _ in COUNTRY_CHOICES}
    return templates.TemplateResponse(request=request, name='user_form.html', context={"request": request, "user": u_dict, "action": f"/users/{user_id}/edit", "countries": COUNTRY_CHOICES, "selected_country": selected or 'HR', "phone_example": ex, "examples_map": examples_map, "user_types": USER_TYPES, "selected_user_type": u_dict.get('user_type','user'), "current_is_admin": is_session_admin(request)})


@app.post('/users/{user_id}/edit')
def update_user_form(request: Request, user_id: int, name: str = Form(None), phone: str = Form(None), country: str = Form('HR'), username: str = Form(...), email: str = Form(None), password: str = Form(None), user_type: str = Form('user'), permanent: str = Form(None)):
    r = require_admin(request)
    if r:
        return r

    try:
        # Validate inputs
        validate_name(name)
        validate_username(username)
        if password:
            validate_password(password, username)
        if phone:
            validate_phone(phone, country)

        pwd = None
        if password:
            pwd = pwd_context.hash(password)

        phone_e164 = None
        if phone:
            # Normalize when possible; if parsing fails, and phone is 9 digits, prepend country dial code to form E.164
            try:
                normalized = normalize_phone(phone, default_region=country)
                phone_e164 = normalized['e164']
            except Exception:
                # fallback for 9-digit national numbers: build +<dial><digits>
                if phone.isdigit() and len(phone) == 9:
                    dial = DIAL_CODES.get(country)
                    if dial:
                        phone_e164 = f"+{dial}{phone}"
                    else:
                        phone_e164 = None
                else:
                    phone_e164 = None

        # Determine existing username, user_type & permanent flag
        existing = db.get_user(user_id)
        try:
            existing_username = dict(existing).get('username') if existing else None
            existing_permanent = int(dict(existing).get('permanent', 0)) if existing else 0
            existing_user_type = dict(existing).get('user_type') if existing else None
        except Exception:
            existing_username = existing[1] if existing and len(existing) > 1 else None
            existing_permanent = int(existing[8]) if existing and len(existing) > 8 else 0
            existing_user_type = existing[7] if existing and len(existing) > 7 else None

        # If account is already permanent, never allow unsetting it and never allow changing the account type
        if existing_permanent:
            permanent_flag = 1
            # keep existing type
            if existing_user_type:
                user_type = existing_user_type
        else:
            # Not permanent yet — accept checkbox to set it
            permanent_flag = 1 if permanent == '1' else 0
            # If editing the 'admin' username, keep it admin and force permanent
            if existing_username == 'admin':
                user_type = 'admin'
                permanent_flag = 1

        try:
            db.update_user(user_id, username=username, email=email, name=name, phone=phone, phone_e164=phone_e164, password_hash=pwd, user_type=user_type, permanent=permanent_flag)
        except Exception:
            with db.connect() as conn:
                cur = conn.cursor()
                # fallback: update phone_e164 directly if update_user not present
                cur.execute('UPDATE users SET username=?, email=?, name=?, phone=?, phone_e164=?, password_hash=?, user_type=?, permanent=? WHERE id = ?', (username, email, name, phone, phone_e164, pwd, user_type, permanent_flag, user_id))
                conn.commit()
        return RedirectResponse('/users?msg=User+updated', status_code=303)
    except Exception as e:
        u = db.get_user(user_id)
        u_dict = dict(u) if u else None
        ex = example_for_country(country)
        examples_map = {code: example_for_country(code)['display'] for code, _ in COUNTRY_CHOICES}
        return templates.TemplateResponse(request=request, name='user_form.html', context={"request": request, "user": u_dict, "error": str(e), "action": f"/users/{user_id}/edit", "countries": COUNTRY_CHOICES, "selected_country": country, "phone_example": ex, "examples_map": examples_map, "user_types": USER_TYPES, "selected_user_type": user_type, "current_is_admin": is_session_admin(request)})


@app.get('/users/{user_id}/delete', response_class=HTMLResponse)
def confirm_delete_page(request: Request, user_id: int):
    r = require_admin(request)
    if r:
        return r

    u = db.get_user(user_id)
    if not u:
        return RedirectResponse('/users?msg=User+not+found', status_code=303)
    ud = dict(u) if not isinstance(u, dict) else u

    # Admin account cannot be deleted
    if ud.get('username') == 'admin':
        return RedirectResponse('/users?msg=Cannot+delete+admin', status_code=303)

    # Only show confirmation when account is permanent
    if not int(ud.get('permanent', 0)):
        return RedirectResponse('/users?msg=Use+Delete+button+to+remove+this+account', status_code=303)

    return templates.TemplateResponse(request=request, name='confirm_delete.html', context={"request": request, "user": ud, "error": None})


@app.post('/users/{user_id}/delete')
def delete_user_form(request: Request, user_id: int, admin_password: str = Form(None)):
    r = require_admin(request)
    if r:
        return r

    existing = db.get_user(user_id)
    if not existing:
        return RedirectResponse('/users?msg=User+not+found', status_code=303)

    try:
        e = dict(existing) if not isinstance(existing, dict) else existing
        existing_username = e.get('username')
        existing_permanent = int(e.get('permanent', 0))
    except Exception:
        existing_username = existing[1] if existing and len(existing) > 1 else None
        existing_permanent = int(existing[8]) if existing and len(existing) > 8 else 0

    # Admin account cannot be deleted
    if existing_username == 'admin':
        return RedirectResponse('/users?msg=Cannot+delete+admin', status_code=303)

    # Deleting a permanent account requires admin password confirmation
    if existing_permanent:
        # If no password provided, render confirmation form
        if not admin_password:
            ud = dict(existing) if not isinstance(existing, dict) else existing
            return templates.TemplateResponse(request=request, name='confirm_delete.html', context={"request": request, "user": ud, "error": None})

        # Verify the password for the current session admin
        current = request.session.get('user')
        admin_user = db.get_user_by_username(current)
        stored_hash = None
        try:
            stored_hash = dict(admin_user).get('password_hash') if admin_user else None
        except Exception:
            try:
                stored_hash = admin_user['password_hash']
            except Exception:
                try:
                    stored_hash = admin_user[-1]
                except Exception:
                    stored_hash = None

        if not stored_hash or not pwd_context.verify(admin_password, stored_hash):
            ud = dict(existing) if not isinstance(existing, dict) else existing
            return templates.TemplateResponse(request=request, name='confirm_delete.html', context={"request": request, "user": ud, "error": "Invalid admin password"})

        # Password ok; proceed to delete
        try:
            db.delete_user(user_id)
            return RedirectResponse('/users?msg=User+deleted', status_code=303)
        except Exception as e:
            return RedirectResponse(f'/users?msg=Delete+failed:+{e}', status_code=303)

    # Non-permanent accounts: proceed to delete directly
    try:
        db.delete_user(user_id)
        return RedirectResponse('/users?msg=User+deleted', status_code=303)
    except Exception as e:
        rows = db.get_all_users()
        users = []
        for r in rows:
            try:
                users.append(dict(r) if not isinstance(r, dict) else r)
            except Exception:
                users.append({'id': r[0], 'username': r[1], 'email': r[2]})
        return templates.TemplateResponse(request=request, name='users.html', context={"request": request, "users": users, "msg": None, "error": str(e)})

@app.get("/users/{user_id}")
def read_user(user_id: int):
    user = db.get_user(user_id)
    if not user:
        return {"error": "User not found"}
    return {
        "id": user[0],
        "username": user[1],
        "email": user[2],
        "created_at": user[3]
    }

# Secret key for browser sessions
app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_KEY")
# Session timeout in seconds (default 30 minutes)
SESSION_TIMEOUT_SECONDS = int(os.environ.get('SESSION_TIMEOUT', 60*30))
# Whether the persistent 'remember_user' cookie should bypass inactivity timeout ("1" true, "0" false)
REMEMBER_PERSISTS_TIMEOUT = os.environ.get('REMEMBER_PERSISTS_TIMEOUT', '0') == '1'

# Helper: check session user is admin
def is_session_admin(request: Request) -> bool:
    try:
        username = request.session.get("user")
        if not username:
            return False
        user = db.get_user_by_username(username)
        if not user:
            return False
        u = dict(user) if not isinstance(user, dict) else user
        return u.get('user_type') == 'admin'
    except Exception:
        return False


def require_admin(request: Request):
    """Return a RedirectResponse if the current request is not from an admin; otherwise None."""
    if 'user' not in request.session:
        return RedirectResponse('/login')
    if not is_session_admin(request):
        return RedirectResponse('/?msg=Not+authorized', status_code=303)
    return None

# Helper: get current username for templates
from datetime import date, timedelta, datetime

def get_current_user(request: Request):
    try:
        return request.session.get('user')
    except Exception:
        return None

# Expose helper to templates so templates can call get_current_user(request)
templates.env.globals['get_current_user'] = get_current_user

# Simple translations dictionary (English 'en' and Croatian 'hr')
TRANSLATIONS = {
    'en': {
        'home': 'Home', 'track': 'Track', 'insights': 'Insights', 'daily_co2': 'Daily CO₂', 'eco_score': 'Eco Score', 'gps_tracking': 'GPS Tracking',
        'log_in': 'Log In', 'sign_up': 'Sign Up', 'profile': 'Profile', 'logout': 'Log out', 'welcome': 'Welcome to EcoCode', 'welcome_back': 'Welcome back, {username}',
        'quick_links': 'Quick links', 'start': 'Start', 'stop': 'Stop', 'save': 'Save', 'enable_location': 'Enable location', 'no_saved_tracks': 'No saved tracks yet.', 'quick_tracking': 'Quick tracking', 'no_activities_tracked': 'No activities tracked yet.',
        'language': 'Language', 'english': 'English', 'croatian': 'Croatian', 'save_changes': 'Save changes', 'name': 'Name', 'email': 'Email', 'phone': 'Phone', 'start_a_new_track': 'Start a new track on the GPS tracking page and save it to your account.', 'create_account': 'Create account', 'username': 'Username', 'password': 'Password', 'confirm_password': 'Confirm password', 'already_have_account': 'Already have an account? Log in', 'country': 'Country',
        # GPS / tracking specific
        'activity': 'Activity', 'bike': 'Bike', 'hike': 'Hike', 'walk': 'Walk', 'track_name_placeholder': 'Morning ride', 'distance': 'Distance', 'points': 'Points', 'time': 'Time', 'saved_tracks': 'Saved tracks', 'tips': 'Tips', 'clear': 'Clear',
        'tips_allow_location': 'Allow location permission and enable high accuracy for best results.', 'tips_stop_before_save': 'Stop tracking before saving to mark an end time.', 'tips_saved_private': 'Saved tracks are private to your account.',
        'no_points_to_save': 'No points to save', 'saved_track': 'Saved track', 'save_failed': 'Save failed', 'error_saving': 'Error saving:', 'cannot_load_track': 'Cannot load track:', 'no_points': 'No points',
        'location_not_supported': 'Geolocation is not supported in this browser.', 'permission_granted_msg': 'Location permission granted. You can now Start tracking.', 'permission_denied_msg': 'Location permission denied. Please enable location access in your browser settings.', 'could_not_get_location': 'Could not get location:' , 'view': 'View',
        'cookie_message': 'Diese Website verwendet Cookies, um Ihnen das beste Erlebnis zu bieten.',
        'cookie_dismiss': 'Verstanden!',
        'cookie_link': 'Mehr erfahren'
    },
    'hr': {
        'home': 'Početna', 'track': 'Praćenje', 'insights': 'Uvidi', 'daily_co2': 'Dnevni CO₂', 'eco_score': 'Eko rezultat', 'gps_tracking': 'GPS praćenje',
        'log_in': 'Prijava', 'sign_up': 'Registracija', 'profile': 'Profil', 'logout': 'Odjava', 'welcome': 'Dobrodošli u EcoCode', 'welcome_back': 'Dobrodošli, {username}',
        'quick_links': 'Brze poveznice', 'start': 'Pokreni', 'stop': 'Zaustavi', 'save': 'Spremi', 'enable_location': 'Omogući lokaciju', 'no_saved_tracks': 'Još nema spremljenih ruta.', 'quick_tracking': 'Brzo praćenje', 'no_activities_tracked': 'Još nema zabilježenih aktivnosti.',
        'language': 'Jezik', 'english': 'Engleski', 'croatian': 'Hrvatski', 'save_changes': 'Spremi promjene', 'name': 'Ime', 'email': 'E-pošta', 'phone': 'Telefon', 'start_a_new_track': 'Započnite novu rutu na GPS stranici i spremite je na svoj račun.', 'create_account': 'Stvori račun', 'username': 'Korisničko ime', 'password': 'Lozinka', 'confirm_password': 'Potvrdite lozinku', 'already_have_account': 'Već imate račun? Prijavite se', 'country': 'Država',
        # GPS / tracking specific
        'activity': 'Aktivnost', 'bike': 'Bicikl', 'hike': 'Planinarenje', 'walk': 'Hodanje', 'track_name_placeholder': 'Jutarnja vožnja', 'distance': 'Udaljenost', 'points': 'Točke', 'time': 'Vrijeme', 'saved_tracks': 'Spremljene rute', 'tips': 'Savjeti', 'clear': 'Očisti',
        'tips_allow_location': 'Dopustite pristup lokaciji i omogućite visoku točnost za najbolje rezultate.', 'tips_stop_before_save': 'Zaustavite praćenje prije spremanja kako biste označili završetak.', 'tips_saved_private': 'Spremljene rute su privatne za vaš račun.',
        'no_points_to_save': 'Nema točaka za spremanje', 'saved_track': 'Ruta spremljena', 'save_failed': 'Spremanje nije uspjelo', 'error_saving': 'Pogreška pri spremanju:', 'cannot_load_track': 'Ne mogu učitati rutu:', 'no_points': 'Nema točaka',
        'location_not_supported': 'Geolokacija nije podržana u ovom pregledniku.', 'permission_granted_msg': 'Dopuštenje za lokaciju je omogućeno. Sada možete pokrenuti praćenje.', 'permission_denied_msg': 'Dopuštenje za lokaciju odbijeno. Molimo omogućite pristup lokaciji u postavkama preglednika.', 'could_not_get_location': 'Ne mogu dobiti lokaciju:', 'view': 'Pogledaj'
    }
}


def get_language_for_request(request: Request):
    # Priority: session lang, then user preference in DB, else 'en'
    try:
        lang = request.session.get('lang')
        if lang:
            return lang
        if 'user' in request.session:
            username = request.session.get('user')
            user = db.get_user_by_username(username)
            if user:
                try:
                    u = dict(user) if not isinstance(user, dict) else user
                    lang = u.get('language')
                    if lang:
                        # cache in session
                        try:
                            request.session['lang'] = lang
                        except Exception:
                            pass
                        return lang
                except Exception:
                    pass
    except Exception:
        pass
    return 'en'


def t(request: Request, key: str, **kwargs):
    lang = get_language_for_request(request)
    txt = TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, TRANSLATIONS['en'].get(key, key))
    try:
        return txt.format(**kwargs)
    except Exception:
        return txt

# expose to templates
templates.env.globals['t'] = t


# ---------- Metrics helper ----------
# Large tip list (100 tips)
TIP_LIST = [
    "Turn off lights when leaving a room.",
    "Unplug chargers when not in use.",
    "Use LED bulbs instead of old bulbs.",
    "Lower your heating by 1°C.",
    "Air‑dry clothes instead of using a dryer.",
    "Wash clothes in cold water.",
    "Enable power‑saving mode on devices.",
    "Take shorter showers.",
    "Fix leaking taps.",
    "Use smart plugs to cut standby power.",
    "Choose energy‑efficient appliances.",
    "Cook with lids on pots.",
    "Boil only the water you need.",
    "Use natural light during the day.",
    "Clean fridge coils for better efficiency.",
    "Defrost your freezer regularly.",
    "Turn off your PC instead of sleep mode.",
    "Use a fan instead of AC when possible.",
    "Insulate windows and doors.",
    "Charge devices during the day using solar if possible.",
    "Walk short distances instead of driving.",
    "Bike to work once a week.",
    "Use public transport when available.",
    "Carpool with friends or coworkers.",
    "Combine errands into one trip.",
    "Avoid idling your car.",
    "Keep tires properly inflated.",
    "Drive smoothly and avoid hard braking.",
    "Remove roof racks when not needed.",
    "Use cruise control on highways.",
    "Choose fuel‑efficient routes.",
    "Avoid rush hour when possible.",
    "Share rides to events.",
    "Try an electric scooter.",
    "Use car‑sharing services.",
    "Plan vacations closer to home.",
    "Avoid unnecessary flights.",
    "Choose trains over planes for short trips.",
    "Work from home once a week.",
    "Maintain your car regularly.",
    "Eat one plant‑based meal today.",
    "Reduce beef consumption.",
    "Choose seasonal fruits and vegetables.",
    "Buy local produce.",
    "Avoid food waste by planning meals.",
    "Store food properly to avoid spoilage.",
    "Freeze leftovers instead of throwing them away.",
    "Use reusable containers.",
    "Bring your own shopping bag.",
    "Choose products with minimal packaging.",
    "Drink tap water instead of bottled.",
    "Reduce sugary drinks.",
    "Make your own snacks.",
    "Compost food scraps.",
    "Grow herbs at home.",
    "Choose whole foods over processed.",
    "Avoid single‑use cutlery.",
    "Buy in bulk when possible.",
    "Support eco‑friendly brands.",
    "Try a “meat‑free Monday.”",
    "Recycle paper, plastic, and glass.",
    "Donate old clothes instead of throwing them away.",
    "Repair items instead of replacing them.",
    "Buy second‑hand when possible.",
    "Avoid fast fashion.",
    "Use reusable water bottles.",
    "Use reusable coffee cups.",
    "Switch to eco‑friendly cleaning products.",
    "Avoid microplastic‑heavy cosmetics.",
    "Use cloth towels instead of paper.",
    "Turn off the tap while brushing teeth.",
    "Use a dishwasher instead of hand washing.",
    "Wash full loads only.",
    "Choose biodegradable soaps.",
    "Avoid glitter (it’s microplastic).",
    "Use rechargeable batteries.",
    "Borrow tools instead of buying.",
    "Choose digital receipts.",
    "Reduce junk mail subscriptions.",
    "Buy long‑lasting products.",
    "Lower screen brightness.",
    "Use dark mode to save battery.",
    "Delete unused apps.",
    "Extend device lifespan with proper care.",
    "Recycle old electronics responsibly.",
    "Use cloud storage efficiently.",
    "Avoid unnecessary video streaming.",
    "Download music instead of streaming repeatedly.",
    "Turn off Bluetooth when not needed.",
    "Use Wi‑Fi instead of mobile data.",
    "Set a weekly eco goal.",
    "Track your CO₂ footprint daily.",
    "Celebrate small wins.",
    "Teach someone one eco habit.",
    "Join a local cleanup event.",
    "Follow eco‑friendly creators.",
    "Learn one new sustainability fact weekly.",
    "Choose quality over quantity.",
    "Think before buying — “Do I need this?”",
    "Make one small change today."
]

def get_user_metrics(user):
    """Return metrics derived from user activities. Defaults are zero until the user adds activities."""
    if not user:
        return {}
    try:
        uid = int(user.get('id')) if isinstance(user, dict) else None
        username = user.get('username') if isinstance(user, dict) else str(user)
    except Exception:
        uid = None
        username = str(user)

    today = date.today()
    days = 7
    start_date = (today - timedelta(days=days-1)).isoformat()
    end_date = today.isoformat()

    activity_by_day = {}
    try:
        if uid is not None:
            activity_by_day = db.get_activity_sums_by_day(uid, start_date, end_date)
    except Exception:
        activity_by_day = {}

    last7 = []
    CAR_FACTOR = 0.192  # baseline car (kg/km) used to estimate savings for bike/walk
    try:
        if uid is not None:
            for i in range(days-1, -1, -1):
                d = today - timedelta(days=i)
                day_str = d.isoformat()
                # fetch per-day activities
                rows = db.get_activities_for_user_on_date(uid, day_str)
                emitted = 0.0
                saved = 0.0
                for r in rows:
                    try:
                        a = dict(r) if not isinstance(r, dict) else r
                        co2 = float(a.get('co2_kg') or 0)
                        qty = a.get('quantity')
                        # compute missing co2 using factor if available
                        if (not co2 or co2 == 0) and qty is not None:
                            try:
                                ef = db.get_emission_factor(a.get('category'), a.get('subtype'))
                                if ef and ef.get('co2_kg_per_unit') is not None:
                                    co2 = float(qty) * float(ef.get('co2_kg_per_unit'))
                            except Exception:
                                pass
                        # negative co2 counts as saved
                        if co2 < 0:
                            saved += abs(co2)
                        elif co2 == 0 and a.get('category') == 'Transport' and (a.get('subtype') in ('Bicikl', 'Hodanje')):
                            try:
                                saved += float(qty or 0) * CAR_FACTOR
                            except Exception:
                                pass
                        else:
                            emitted += co2
                    except Exception:
                        continue
                net = round(emitted - saved, 3)
                last7.append({'date': day_str, 'emitted_kg': round(emitted,3), 'saved_kg': round(saved,3), 'net_kg': net})
        else:
            for i in range(days-1, -1, -1):
                d = today - timedelta(days=i)
                day_str = d.isoformat()
                last7.append({'date': day_str, 'emitted_kg': 0.0, 'saved_kg': 0.0, 'net_kg': 0.0})
    except Exception:
        # fallback to previous aggregation if something fails
        last7 = []
        for i in range(days-1, -1, -1):
            d = today - timedelta(days=i)
            day_str = d.isoformat()
            activity_val = round(activity_by_day.get(day_str, 0.0), 2)
            last7.append({'date': day_str, 'emitted_kg': activity_val, 'saved_kg': 0.0, 'net_kg': activity_val})

    # Use today's net CO₂ for daily_co2
    daily_co2 = last7[-1]['net_kg'] if last7 else 0.0
    # Default eco_score to 0 when there's no recorded activity; otherwise compute from CO₂
    if daily_co2 == 0:
        eco_score = 0
    else:
        eco_score = int(max(0, min(100, 100 - daily_co2 * 3)))
    quick_tips = ["Bring a reusable bag today", "Avoid single-use plastic", "Try biking for short trips"]
    streak_days = 0
    try:
        if uid is not None:
            counts = db.get_activity_counts_by_day(uid, (today - timedelta(days=365)).isoformat(), end_date)
        else:
            counts = {}
        streak = 0
        d = today
        for _ in range(365):
            s = d.isoformat()
            if counts.get(s, 0) > 0:
                streak += 1
                d = d - timedelta(days=1)
            else:
                break
        streak_days = streak
    except Exception:
        streak_days = 0

    # Compute today's emitted and saved CO₂ robustly on the server so clients get a consistent view.
    today_emitted = 0.0
    today_saved = 0.0
    try:
        if uid is not None:
            rows = db.get_activities_for_user(uid, limit=1000)
            today_str = today.isoformat()
            CAR_FACTOR = 0.192  # baseline car (kg/km) used to estimate savings for bike/walk
            for r in rows:
                a = dict(r) if not isinstance(r, dict) else r
                created = a.get('created_at') or ''
                if not created.startswith(today_str):
                    continue
                co2 = float(a.get('co2_kg') or 0)
                qty = a.get('quantity')
                # If stored co2 is zero or missing, try to compute using emission factor
                if (not co2 or co2 == 0) and qty is not None:
                    try:
                        ef = db.get_emission_factor(a.get('category'), a.get('subtype'))
                        if ef and ef.get('co2_kg_per_unit') is not None:
                            co2 = float(qty) * float(ef.get('co2_kg_per_unit'))
                    except Exception:
                        pass
                if co2 < 0:
                    today_saved += abs(co2)
                elif co2 == 0 and a.get('category') == 'Transport' and (a.get('subtype') in ('Bicikl', 'Hodanje')):
                    try:
                        today_saved += float(qty or 0) * CAR_FACTOR
                    except Exception:
                        pass
                else:
                    today_emitted += co2
    except Exception:
        today_emitted = 0.0
        today_saved = 0.0

    achievements = []
    if streak_days >= 7:
        achievements.append("First week streak")
    if streak_days >= 30:
        achievements.append("30 day streak")

    notifications = [f"You saved {round(today_saved,2)} kg CO₂ today"]
    return {
        'daily_co2': daily_co2,
        'today_emitted': round(today_emitted, 3),
        'today_saved': round(today_saved, 3),
        'eco_score': eco_score,
        'quick_tips': quick_tips,
        'streak_days': streak_days,
        'achievements': achievements,
        'last7': last7,
        'notifications': notifications
    }

# Middleware to restore session from persistent cookie if present
@app.middleware("http")
async def restore_session_from_cookie(request: Request, call_next):
    # Guard: SessionMiddleware may not have been installed yet in some test contexts
    try:
        if 'user' not in request.session:
            remember = request.cookies.get('remember_user')
            if remember:
                # If remember cookie exists, decide whether to restore session based on config
                restored = False
                try:
                    if REMEMBER_PERSISTS_TIMEOUT:
                        restored = True
                    else:
                        # Check user's last_active time in DB; if within timeout, restore; otherwise mark cookie for deletion
                        try:
                            urow = db.get_user_by_username(remember)
                            if urow:
                                u = dict(urow) if not isinstance(urow, dict) else urow
                                last = u.get('last_active')
                                if last:
                                    try:
                                        last_dt = datetime.fromisoformat(last)
                                        if (datetime.now() - last_dt).total_seconds() <= SESSION_TIMEOUT_SECONDS:
                                            restored = True
                                    except Exception:
                                        # If parsing fails, conservatively do not restore
                                        restored = False
                        except Exception:
                            restored = False
                except Exception:
                    restored = False

                if restored:
                    request.session['user'] = remember
                    # set last_active so timeout is tracked
                    try:
                        request.session['last_active'] = time.time()
                    except Exception:
                        pass
                else:
                    # mark to delete the persistent cookie on the response
                    try:
                        request.state.delete_remember_cookie = True
                    except Exception:
                        pass
    except Exception:
        # Session not available — skip
        pass
    response = await call_next(request)
    # Delete persistent cookie if we flagged it earlier
    try:
        if getattr(request.state, 'delete_remember_cookie', False):
            response.delete_cookie('remember_user')
    except Exception:
        pass
    return response

# Middleware to enforce session inactivity timeout
@app.middleware("http")
async def enforce_session_timeout(request: Request, call_next):
    try:
        timeout = int(SESSION_TIMEOUT_SECONDS)
        if 'user' in request.session:
            last = request.session.get('last_active')
            now_ts = time.time()
            if last is not None:
                try:
                    last_ts = float(last)
                except Exception:
                    last_ts = now_ts
                if now_ts - last_ts > timeout:
                    # session timed out
                    request.session.clear()
                    # clear persistent cookie as well
                    # For API requests return 401 JSON, else redirect to login
                    if request.url.path.startswith('/api/'):
                        from fastapi.responses import JSONResponse
                        resp = JSONResponse({"error": "Session timed out"}, status_code=401)
                        resp.delete_cookie('remember_user')
                        return resp
                    else:
                        from fastapi.responses import RedirectResponse
                        resp = RedirectResponse('/login?msg=Session+timed+out')
                        resp.delete_cookie('remember_user')
                        return resp
            # update last_active to now for active session
            try:
                request.session['last_active'] = now_ts
            except Exception:
                pass
    except Exception:
        pass
    response = await call_next(request)
    return response
# -----------------------------
# ROUTES
# -----------------------------
# We now use the centralized Database in `database.py` (db) for all user storage.

def home_duplicate(request: Request):
    # This is a duplicate route - the actual home route is earlier in the file
    show = is_session_admin(request)
    lang = get_lang(request)
    t_dict = translations.get(lang, translations['en'])
    if 'user' in request.session:
        username = request.session.get('user')
        user = db.get_user_by_username(username)
        u = dict(user) if user else None
        metrics = get_user_metrics(u)
        session_tips = request.session.get('tips')
        return templates.TemplateResponse(request=request, name="home.html", context={"request": request, "show_devtools": show, "user": u, "metrics": metrics, "session_tips": session_tips, "t": t_dict, "lang": lang})
    return templates.TemplateResponse(request=request, name="home.html", context={"request": request, "show_devtools": show, "user": None, "metrics": {}, "t": t_dict, "lang": lang})


@app.get("/devtools", response_class=HTMLResponse)
def devtools_page(request: Request):
    # if not logged in, redirect to login
    if 'user' not in request.session:
        return RedirectResponse('/login')

    # logged in but not admin: show the page with a contact message
    if not is_session_admin(request):
        return templates.TemplateResponse(request=request, name="developer_tools.html", context={"request": request, "error": "Contact admin to gain access"})

    # admin: full access
    return templates.TemplateResponse(request=request, name="developer_tools.html", context={"request": request})


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    lang = get_lang(request)
    t_dict = translations.get(lang, translations['en'])
    ex = example_for_country('HR')
    examples_map = {code: example_for_country(code)['display'] for code, _ in COUNTRY_CHOICES}
    return templates.TemplateResponse(request=request, name="signup.html", context={"request": request, "countries": COUNTRY_CHOICES, "selected_country": 'HR', "phone_example": ex, "examples_map": examples_map, "name": '', "phone": '', "username": '', "t": t_dict, "lang": lang})


@app.post("/signup")
def signup(request: Request, name: str = Form(...),
           email: str = Form(...),
           phone: str = Form(None),
           country: str = Form('HR'),
           username: str = Form(...),
           password: str = Form(...),
           password_confirm: str = Form(...)):

    # Validate inputs
    try:
        validate_name(name)
        validate_username(username)
        if not email or not email.strip():
            raise ValueError('Email is required')
        # ensure passwords match
        if password != password_confirm:
            raise ValueError('Passwords do not match')
        validate_password(password, username)
        if phone:
            validate_phone(phone, country)
    except Exception as e:
        ex = example_for_country(country)
        examples_map = {code: example_for_country(code)['display'] for code, _ in COUNTRY_CHOICES}
        return templates.TemplateResponse(request=request, name="signup.html", context={"request": request, "error": str(e), "countries": COUNTRY_CHOICES, "selected_country": country, "phone_example": ex, "examples_map": examples_map, "name": name, "phone": phone, "username": username, "email": email})

    # Check if username or email exists
    if db.get_user_by_username(username) or db.get_user_by_login(email):
        ex = example_for_country(country)
        examples_map = {code: example_for_country(code)['display'] for code, _ in COUNTRY_CHOICES}
        return templates.TemplateResponse(request=request, name="signup.html", context={"request": request, "error": "Username or email already exists", "countries": COUNTRY_CHOICES, "selected_country": country, "phone_example": ex, "examples_map": examples_map, "name": name, "phone": phone, "username": username, "email": email})

    # Save user (store password hash in users.password_hash)
    try:
        if phone:
            # Normalize provided phone using selected country when possible
            try:
                normalized = normalize_phone(phone, default_region=country)
                phone_e164 = normalized['e164']
            except Exception:
                # fallback: if phone is 9 digits, prepend dial code
                if phone.isdigit() and len(phone) == 9:
                    dial = DIAL_CODES.get(country)
                    if dial:
                        phone_e164 = f"+{dial}{phone}"
                    else:
                        phone_e164 = None
                else:
                    phone_e164 = None
        else:
            phone_e164 = None

        hashed = pwd_context.hash(password)
        new_id = db.add_user(username=username, email=email, name=name, phone=phone, password_hash=hashed, user_type='user')
        if phone_e164:
            try:
                db.update_user(new_id, phone_e164=phone_e164)
            except Exception:
                with db.connect() as conn:
                    cur = conn.cursor()
                    cur.execute('UPDATE users SET phone_e164 = ? WHERE id = ?', (phone_e164, new_id))
                    conn.commit()
    except Exception as e:
        ex = example_for_country(country)
        examples_map = {code: example_for_country(code)['display'] for code, _ in COUNTRY_CHOICES}
        return templates.TemplateResponse(request=request, name="signup.html", context={"request": request, "error": str(e), "countries": COUNTRY_CHOICES, "selected_country": country, "phone_example": ex, "examples_map": examples_map, "name": name, "phone": phone, "username": username, "email": email})

    return RedirectResponse("/login", status_code=302)


@app.get("/eula", response_class=HTMLResponse)
@app.get("/eula.html", response_class=HTMLResponse)
def eula_page(request: Request):
    """Render the EULA page (accessible at /eula and /eula.html)."""
    lang = get_lang(request)
    t_dict = translations.get(lang, translations['en'])
    show = is_session_admin(request)
    return templates.TemplateResponse(request=request, name="eula.html", context={"request": request, "t": t_dict, "lang": lang, "show_devtools": show})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    lang = get_lang(request)
    t_dict = translations.get(lang, translations['en'])
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "t": t_dict, "lang": lang})


@app.post("/login")
def login(request: Request,
          who: str = Form(...),
          password: str = Form(...)):

    user = db.get_user_by_login(who)

    if not user:
        return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": "Invalid username or password"})

    # Get stored password hash (use mapping when possible)
    try:
        stored_hash = user['password_hash']
    except Exception:
        # fallback: assume the last column is password_hash in older schemas
        try:
            stored_hash = user[-1]
        except Exception:
            stored_hash = None

    if not stored_hash or not pwd_context.verify(password, stored_hash):
        return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": "Invalid username or password"})

    # Save login session using canonical username
    try:
        username = user['username'] or who
    except Exception:
        username = who
    request.session["user"] = username
    # set session last_active for inactivity tracking
    try:
        request.session['last_active'] = time.time()
    except Exception:
        pass

    # update last_active timestamp for this user in DB
    try:
        # determine user id from the returned row
        try:
            uid = dict(user).get('id')
        except Exception:
            uid = user[0] if user and len(user) > 0 else None
        if uid:
            db.update_user(uid, last_active=datetime.now().isoformat())
    except Exception:
        pass

    # choose three tips for this login and store in session so it persists until logout
    try:
        # use a time-based seed so each login produces different tips
        random.seed(time.time_ns() ^ hash(username))
        chosen = random.sample(TIP_LIST, 3)
    except Exception:
        chosen = TIP_LIST[:3]
    request.session['tips'] = chosen
    # set session language from user preference if available
    try:
        lang = None
        try:
            lang = dict(user).get('language') if user else None
        except Exception:
            try:
                lang = user['language']
            except Exception:
                lang = None
        if lang:
            request.session['lang'] = lang
    except Exception:
        pass

    # create a persistent cookie so session persists across browser restarts (30 days)
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie("remember_user", username, max_age=60*60*24*30)
    return resp


@app.post('/api/login')
async def api_login(request: Request):
    data = await request.json()
    who = data.get('who') or data.get('username') or data.get('login')
    password = data.get('password')
    if not who or not password:
        return JSONResponse({"error": "Missing login credentials"}, status_code=400)
    user = db.get_user_by_login(who)
    if not user:
        return JSONResponse({"error": "Invalid username or password"}, status_code=401)
    try:
        stored_hash = user['password_hash']
    except Exception:
        try:
            stored_hash = user[-1]
        except Exception:
            stored_hash = None
    if not stored_hash or not pwd_context.verify(password, stored_hash):
        return JSONResponse({"error": "Invalid username or password"}, status_code=401)
    # create token
    try:
        uid = dict(user).get('id')
    except Exception:
        uid = user[0] if user and len(user) > 0 else None
    if not uid:
        return JSONResponse({"error": "Account retrieval failed"}, status_code=500)
    token = db.create_api_token(uid)
    return {"access_token": token, "token_type": "bearer", "id": uid, "username": dict(user).get('username')}



    email = data.get('email')
    phone = data.get('phone')
    country = data.get('country', 'HR')
    username = data.get('username')
    password = data.get('password')
    password_confirm = data.get('password_confirm')

    try:
        validate_name(name)
        validate_username(username)
        if not email or not email.strip():
            raise ValueError('Email is required')
        if password != password_confirm:
            raise ValueError('Passwords do not match')
        validate_password(password, username)
        if phone:
            validate_phone(phone, country)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    if db.get_user_by_username(username) or db.get_user_by_login(email):
        return JSONResponse({"error": "Username or email already exists"}, status_code=400)

    try:
        phone_e164 = None
        if phone:
            try:
                normalized = normalize_phone(phone, default_region=country)
                phone_e164 = normalized['e164']
            except Exception:
                if phone.isdigit() and len(phone) == 9:
                    dial = DIAL_CODES.get(country)
                    if dial:
                        phone_e164 = f"+{dial}{phone}"
        hashed = pwd_context.hash(password)
        new_id = db.add_user(username=username, email=email, name=name, phone=phone, password_hash=hashed, user_type='user')
        if phone_e164:
            try:
                db.update_user(new_id, phone_e164=phone_e164)
            except Exception:
                with db.connect() as conn:
                    cur = conn.cursor()
                    cur.execute('UPDATE users SET phone_e164 = ? WHERE id = ?', (phone_e164, new_id))
                    conn.commit()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    token = db.create_api_token(new_id)
    return {"access_token": token, "token_type": "bearer", "id": new_id, "username": username}


def _get_user_from_header(request: Request):
    auth = request.headers.get('Authorization') or request.headers.get('authorization')
    if not auth:
        return None
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == 'bearer':
        token = parts[1]
        return db.get_user_by_token(token)
    return None

# API helpers: prefer bearer token but fall back to browser session for web clients
def _get_api_user(request: Request):
    """Return user dict for API requests (token preferred, else session user)."""
    try:
        u = _get_user_from_header(request)
        if u:
            return dict(u) if not isinstance(u, dict) else u
    except Exception:
        pass
    try:
        if 'user' in request.session:
            username = request.session.get('user')
            user = db.get_user_by_username(username)
            return dict(user) if user and not isinstance(user, dict) else user
    except Exception:
        pass
    return None

def require_api_user(request: Request):
    u = _get_api_user(request)
    if not u:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return None

def require_api_admin(request: Request):
    u = _get_api_user(request)
    if not u:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    if u.get('user_type') != 'admin':
        return JSONResponse({"error": "Not authorized"}, status_code=403)
    return None


@app.post('/api/logout')
def api_logout(request: Request):
    auth = request.headers.get('Authorization') or request.headers.get('authorization')
    if not auth:
        return JSONResponse({"error": "Missing Authorization header"}, status_code=400)
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return JSONResponse({"error": "Invalid Authorization header"}, status_code=400)
    token = parts[1]
    deleted = db.delete_api_token(token)
    if deleted:
        return {"ok": True}
    return JSONResponse({"error": "Token not found"}, status_code=400)


@app.post('/api/profile')
async def api_profile_update(request: Request):
    api_user = _get_api_user(request)
    if not api_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    data = await request.json()
    updates = {}
    if data.get('name') is not None:
        updates['name'] = data.get('name')
    if data.get('email') is not None:
        updates['email'] = data.get('email')
    if data.get('phone') is not None:
        updates['phone'] = data.get('phone')
    if data.get('language') is not None:
        updates['language'] = data.get('language')
    if data.get('password'):
        try:
            validate_password(data.get('password'), api_user.get('username'))
            updates['password_hash'] = pwd_context.hash(data.get('password'))
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=400)
    if updates:
        try:
            db.update_user(api_user.get('id'), **updates)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
    new_user = db.get_user(api_user.get('id'))
    return {"user": dict(new_user) if new_user else None}


@app.get('/api/me')
def api_me(request: Request):
    u = _get_user_from_header(request)
    if not u:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    ud = dict(u) if not isinstance(u, dict) else u
    return {"id": ud.get('id'), "username": ud.get('username'), "email": ud.get('email'), "name": ud.get('name')}


@app.get("/hello")
def hello(request: Request):
    if "user" not in request.session:
        return RedirectResponse("/login")
    return RedirectResponse("/", status_code=302)


@app.get('/logout')
def logout(request: Request):
    # clear session and remove persistent cookie
    request.session.clear()
    resp = RedirectResponse('/', status_code=302)
    resp.delete_cookie('remember_user')
    return resp


@app.get('/profile', response_class=HTMLResponse)
def profile_page(request: Request):
    if 'user' not in request.session:
        return RedirectResponse('/login')
    username = request.session['user']
    user = db.get_user_by_username(username)
    if not user:
        return RedirectResponse('/login')
    u = dict(user) if not isinstance(user, dict) else user
    # Set default theme if not set
    if 'theme' not in u or u['theme'] is None:
        u['theme'] = 'light'
    show_devtools = is_session_admin(request)
    lang = get_lang(request)
    t = translations[lang]
    return templates.TemplateResponse(request=request, name='profile.html', context={'request': request, 'user': u, 'show_devtools': show_devtools, 't': t, 'lang': lang})


@app.get('/settings', response_class=HTMLResponse)
def settings_page(request: Request):
    if 'user' not in request.session:
        return RedirectResponse('/login')
    username = request.session['user']
    user = db.get_user_by_username(username)
    if not user:
        return RedirectResponse('/login')
    u = dict(user) if not isinstance(user, dict) else user
    lang = get_lang(request)
    t = translations[lang]
    return templates.TemplateResponse(request=request, name='settings.html', context={'request': request, 'user': u, 't': t, 'lang': lang})


@app.post('/profile')
def profile_update(request: Request, language: str = Form(None)):
    if 'user' not in request.session:
        return RedirectResponse('/login')
    username = request.session['user']
    user = db.get_user_by_username(username)
    if not user:
        return RedirectResponse('/login')
    try:
        uid = dict(user).get('id') if not isinstance(user, dict) else user.get('id')
    except Exception:
        uid = user[0] if user and len(user) > 0 else None
    if uid and language:
        try:
            db.update_user(uid, language=language)
            request.session['lang'] = language
        except Exception:
            pass
    return RedirectResponse('/profile', status_code=302)


@app.post('/api/update-theme')
async def update_theme(request: Request):
    """Update user theme preference"""
    if 'user' not in request.session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    username = request.session['user']
    user = db.get_user_by_username(username)
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    try:
        data = await request.json()
        theme = data.get('theme', 'light')
        
        # Validate theme value
        if theme not in ['light', 'dark']:
            return JSONResponse({"error": "Invalid theme"}, status_code=400)
        
        uid = dict(user).get('id') if not isinstance(user, dict) else user.get('id')
        if uid:
            db.update_user(uid, theme=theme)
            return JSONResponse({"success": True, "theme": theme})
        else:
            return JSONResponse({"error": "Could not get user ID"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get('/daily-co2', response_class=HTMLResponse)
def daily_co2_page(request: Request, period: str = Query('hour', alias='range')):
    if 'user' not in request.session:
        return RedirectResponse('/login')
    username = request.session['user']
    user = db.get_user_by_username(username)
    if not user:
        return RedirectResponse('/login')
    u = dict(user) if not isinstance(user, dict) else user
    # fetch data from API helper for requested period
    data = api_user_daily_co2(request, u.get('id'), period)
    if isinstance(data, dict):
        # pass whichever payload exists to template
        context = {'request': request, 'user': u, 'range': data.get('range', period)}
        if data.get('hours') is not None:
            context['date'] = data.get('date')
            context['hours'] = data.get('hours')
        else:
            # points-based ranges
            # set date to today for display
            context['date'] = str(date.today())
            context['points'] = data.get('points')
        lang = get_lang(request)
        t = translations[lang]
        context.update({'t': t, 'lang': lang})
        return templates.TemplateResponse(request=request, name='daily_co2.html', context=context)
    return RedirectResponse('/?msg=Error+loading+data')


@app.get('/eco-score', response_class=HTMLResponse)
def eco_score_page(request: Request, period: str = Query('week', alias='range')):
    if 'user' not in request.session:
        return RedirectResponse('/login')
    username = request.session['user']
    user = db.get_user_by_username(username)
    if not user:
        return RedirectResponse('/login')
    u = dict(user) if not isinstance(user, dict) else user
    data = api_user_eco_scores(request, u.get('id'), period)
    show_devtools = is_session_admin(request)
    lang = get_lang(request)
    t = translations[lang]
    if isinstance(data, dict) and data.get('scores') is not None:
        return templates.TemplateResponse(request=request, name='eco_score.html', context={'request': request, 'user': u, 'range': period, 'scores': data.get('scores'), 'show_devtools': show_devtools, 't': t, 'lang': lang})
    return RedirectResponse('/?msg=Error+loading+data')


# GPS Tracking page (Insights)
@app.get('/insights/gps', response_class=HTMLResponse)
def gps_tracking_page(request: Request):
    if 'user' not in request.session:
        return RedirectResponse('/login')
    username = request.session['user']
    user = db.get_user_by_username(username)
    if not user:
        return RedirectResponse('/login')
    u = dict(user) if not isinstance(user, dict) else user
    try:
        tracks = [dict(r) for r in db.get_tracks_for_user(u.get('id'))]
    except Exception:
        tracks = []
    show_devtools = is_session_admin(request)
    lang = get_lang(request)
    t = translations[lang]
    return templates.TemplateResponse(request=request, name='gps_tracking.html', context={'request': request, 'user': u, 'tracks': tracks, 'show_devtools': show_devtools, 't': t, 'lang': lang})


@app.get('/admin/users/{user_id}/tracks', response_class=HTMLResponse)
def admin_user_tracks_page(request: Request, user_id: int):
    # admin-only
    r = require_admin(request)
    if r:
        return r
    user = db.get_user(user_id)
    if not user:
        return RedirectResponse('/users?msg=User+not+found', status_code=303)
    u = dict(user) if not isinstance(user, dict) else user
    try:
        tracks = [dict(r) for r in db.get_tracks_for_user(user_id)]
    except Exception:
        tracks = []
    return templates.TemplateResponse(request=request, name='admin_user_tracks.html', context={'request': request, 'user': u, 'tracks': tracks})


@app.get('/admin/gps', response_class=HTMLResponse)
def admin_gps_page(request: Request):
    # admin-only
    r = require_admin(request)
    if r:
        return r
    try:
        rows = db.get_all_users()
        users = []
        for row in rows:
            try:
                users.append(dict(row) if not isinstance(row, dict) else row)
            except Exception:
                users.append({'id': row[0], 'username': row[1], 'email': row[2] if len(row) > 2 else ''})
    except Exception:
        users = []
    return templates.TemplateResponse(request=request, name='admin_gps.html', context={'request': request, 'users': users})

@app.post('/admin/tracks/{track_id}/delete')
def admin_delete_track(request: Request, track_id: int):
    # admin-only
    r = require_admin(request)
    if r:
        return r
    owner_id = None
    with db.connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM gps_tracks WHERE id = ?", (track_id,))
        row = cur.fetchone()
        if row:
            try:
                owner_id = row[0]
            except Exception:
                owner_id = row[0] if isinstance(row, (list, tuple)) else None
    try:
        deleted = db.delete_track(track_id)
    except Exception as e:
        return RedirectResponse(f'/users?msg=Delete+failed:+{e}', status_code=303)
    if owner_id:
        return RedirectResponse(f'/admin/users/{owner_id}/tracks', status_code=303)
    return RedirectResponse('/users', status_code=303)


@app.get('/admin/emission_factors', response_class=HTMLResponse)
def admin_emission_factors(request: Request):
    r = require_admin(request)
    if r:
        return r
    try:
        rows = db.list_emission_factors()
        factors = [dict(r) for r in rows]
    except Exception:
        factors = []
    return templates.TemplateResponse(request=request, name='admin_emission_factors.html', context={'request': request, 'factors': factors})


@app.post('/admin/emission_factors')
def admin_create_emission_factor(request: Request, category: str = Form(...), subtype: str = Form(None), unit: str = Form(None), co2_kg_per_unit: float = Form(...), source: str = Form(None), apply_existing: str = Form(None)):
    r = require_admin(request)
    if r:
        return r
    try:
        ef_id = db.upsert_emission_factor(category, subtype, unit, co2_kg_per_unit, source)
        msg = 'Saved.'
        if apply_existing:
            try:
                updated = db.apply_emission_factor_to_activities(category, subtype, co2_kg_per_unit)
                msg = f'Saved and applied to {updated} activities.'
            except Exception as e:
                return RedirectResponse(f'/admin/emission_factors?msg=Partial+error:+{e}', status_code=303)
        return RedirectResponse(f'/admin/emission_factors?msg={msg}', status_code=303)
    except Exception as e:
        return RedirectResponse(f'/admin/emission_factors?msg=Error:+{e}', status_code=303)


@app.get('/admin/activities', response_class=HTMLResponse)
def admin_activities(request: Request):
    r = require_admin(request)
    if r:
        return r
    try:
        rows = db.get_all_activities(limit=1000)
        activities = []
        for rrow in rows:
            try:
                activities.append(dict(rrow) if not isinstance(rrow, dict) else rrow)
            except Exception:
                activities.append({'id': rrow[0], 'user_id': rrow[1], 'username': rrow[2], 'category': rrow[3], 'subtype': rrow[4], 'co2_kg': rrow[5], 'quantity': rrow[6], 'unit': rrow[7], 'note': rrow[8], 'created_at': rrow[9]})
    except Exception:
        activities = []
    return templates.TemplateResponse(request=request, name='admin_activities.html', context={'request': request, 'activities': activities})


@app.post('/admin/activities/{activity_id}/delete')
def admin_delete_activity(request: Request, activity_id: int):
    r = require_admin(request)
    if r:
        return r
    try:
        db.delete_activity(activity_id)
        return RedirectResponse('/admin/activities', status_code=303)
    except Exception as e:
        return RedirectResponse(f'/admin/activities?msg=Delete+failed:+{e}', status_code=303)


@app.get('/debug/tracks')
def debug_get_tracks(request: Request, limit: int = Query(1000)):
    r = require_admin(request)
    if r:
        return r
    try:
        rows = db.get_all_tracks(limit=limit)
        tracks = []
        for rrow in rows:
            try:
                tracks.append(dict(rrow) if not isinstance(rrow, dict) else rrow)
            except Exception:
                tracks.append({'id': rrow[0], 'user_id': rrow[1], 'username': rrow[2] if len(rrow) > 2 else None, 'activity_type': rrow[3], 'name': rrow[4], 'started_at': rrow[5], 'ended_at': rrow[6], 'distance_km': rrow[7], 'created_at': rrow[8]})
        return { 'tracks': tracks }
    except Exception as e:
        return { 'error': str(e) }


@app.post('/debug/tracks')
def debug_create_track(request: Request, user_id: int = Form(...), activity_type: str = Form(None), name: str = Form(None), started_at: str = Form(None), ended_at: str = Form(None), distance_km: float = Form(None)):
    r = require_admin(request)
    if r:
        return r
    try:
        tid = db.add_track(user_id, activity_type or 'walk', name=name, started_at=started_at, ended_at=ended_at, distance_km=distance_km)
        return {'id': tid}
    except Exception as e:
        return {'error': str(e)}


@app.post('/debug/tracks/{track_id}/delete')
def debug_delete_track(request: Request, track_id: int):
    r = require_admin(request)
    if r:
        return r
    try:
        deleted = db.delete_track(track_id)
        return {'deleted': deleted}
    except Exception as e:
        return {'error': str(e)}


@app.post('/debug/tracks/{track_id}/update')
def debug_update_track(request: Request, track_id: int, name: str = Form(None), distance_km: float = Form(None), started_at: str = Form(None), ended_at: str = Form(None), activity_type: str = Form(None)):
    r = require_admin(request)
    if r:
        return r
    try:
        updated = db.update_track(track_id, name=name, distance_km=distance_km, started_at=started_at, ended_at=ended_at, activity_type=activity_type)
        return {'ok': True, 'updated': updated}
    except Exception as e:
        return {'error': str(e)}


@app.get('/debug/tracks/{track_id}/points')
def debug_get_track_points(request: Request, track_id: int):
    r = require_admin(request)
    if r:
        return r
    try:
        rows = db.get_track_points(track_id)
        points = []
        for p in rows:
            try:
                points.append(dict(p) if not isinstance(p, dict) else p)
            except Exception:
                points.append({'seq': p[0], 'lat': p[1], 'lon': p[2], 'timestamp': p[3], 'accuracy': p[4], 'speed': p[5]})
        return {'points': points}
    except Exception as e:
        return {'error': str(e)}


@app.post('/debug/tracks/{track_id}/points')
def debug_add_track_point(request: Request, track_id: int, lat: float = Form(...), lon: float = Form(...), timestamp: str = Form(None), accuracy: float = Form(None), speed: float = Form(None)):
    r = require_admin(request)
    if r:
        return r
    try:
        pts = db.get_track_points(track_id)
        next_seq = 0
        if pts:
            try:
                last = pts[-1]
                next_seq = int(last[0]) + 1
            except Exception:
                next_seq = len(pts)
        pid = db.add_track_point(track_id, next_seq, float(lat), float(lon), timestamp, accuracy, speed)
        return {'ok': True, 'seq': next_seq}
    except Exception as e:
        return {'error': str(e)}


@app.post('/debug/tracks/{track_id}/points/{seq}/delete')
def debug_delete_track_point(request: Request, track_id: int, seq: int):
    r = require_admin(request)
    if r:
        return r
    try:
        deleted = db.delete_track_point(track_id, seq)
        return {'deleted': deleted}
    except Exception as e:
        return {'error': str(e)}


@app.post('/debug/tracks/{track_id}/points/{seq}/update')
def debug_update_track_point(request: Request, track_id: int, seq: int, lat: float = Form(None), lon: float = Form(None), timestamp: str = Form(None), accuracy: float = Form(None), speed: float = Form(None)):
    r = require_admin(request)
    if r:
        return r
    try:
        updated = db.update_track_point(track_id, seq, lat=lat, lon=lon, timestamp=timestamp, accuracy=accuracy, speed=speed)
        return {'ok': True, 'updated': updated}
    except Exception as e:
        return {'error': str(e)}


@app.get('/track', response_class=HTMLResponse)
def track_page(request: Request):
    if 'user' not in request.session:
        return RedirectResponse('/login')
    username = request.session['user']
    user = db.get_user_by_username(username)
    if not user:
        return RedirectResponse('/login')
    u = dict(user) if not isinstance(user, dict) else user
    metrics = get_user_metrics(u)
    # fetch recent activities for display
    activities = [dict(r) for r in db.get_activities_for_user(u.get('id'), limit=100)]
    show_devtools = is_session_admin(request)
    lang = get_lang(request)
    t = translations[lang]
    return templates.TemplateResponse(request=request, name='track.html', context={'request': request, 'user': u, 'metrics': metrics, 'activities': activities, 'show_devtools': show_devtools, 't': t, 'lang': lang})

@app.post('/api/emission_factors')
def api_set_emission_factor(request: Request, category: str = Form(...), subtype: str = Form(None), unit: str = Form(None), co2_kg_per_unit: float = Form(...), source: str = Form(None)):
    """Add or update an emission factor (admin only)."""
    r = require_api_admin(request)
    if r:
        return r
    try:
        ef_id = db.upsert_emission_factor(category, subtype, unit, co2_kg_per_unit, source)
        # notify other pages via response
        return {"ok": True, "id": ef_id}
    except Exception as e:
        return {"error": str(e)}


@app.post('/api/emission_factors/{ef_id}/update')
def api_update_emission_factor(request: Request, ef_id: int, co2_kg_per_unit: float = Form(None), unit: str = Form(None), source: str = Form(None)):
    r = require_api_admin(request)
    if r:
        return r
    try:
        updated = db.update_emission_factor(ef_id, co2_kg_per_unit=co2_kg_per_unit, unit=unit, source=source)
        return {"ok": True, "updated": updated}
    except Exception as e:
        return {"error": str(e)}


@app.post('/api/emission_factors/{ef_id}/delete')
def api_delete_emission_factor(request: Request, ef_id: int):
    r = require_api_admin(request)
    if r:
        return r
    try:
        deleted = db.delete_emission_factor(ef_id)
        return {"deleted": deleted}
    except Exception as e:
        return {"error": str(e)}


@app.post('/api/emission_factors/apply')
def api_apply_emission_factor(request: Request, category: str = Form(...), subtype: str = Form(None), co2_kg_per_unit: float = Form(...)):
    r = require_api_admin(request)
    if r:
        return r
    try:
        updated = db.apply_emission_factor_to_activities(category, subtype, co2_kg_per_unit)
        return {"updated": updated}
    except Exception as e:
        return {"error": str(e)}


# ---------- Activities API ----------
@app.get('/api/activities')
def api_get_activities(request: Request, limit: int = Query(100)):
    api_user = _get_api_user(request)
    if not api_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    u = api_user
    rows = db.get_activities_for_user(u.get('id'), limit)
    acts = []
    for r in rows:
        a = dict(r)
        # If stored co2_kg is zero or null, compute using emission factor * quantity when possible
        co2 = a.get('co2_kg') or 0.0
        qty = a.get('quantity')
        if (not co2 or co2 == 0) and qty is not None:
            try:
                ef = db.get_emission_factor(a.get('category'), a.get('subtype'))
                if ef and ef.get('co2_kg_per_unit') is not None:
                    co2 = round(float(qty) * float(ef.get('co2_kg_per_unit')), 6)
            except Exception:
                pass
        a['co2_kg'] = co2
        acts.append(a)
    return {"activities": acts}


@app.get('/api/emission_factors')
def api_get_emission_factors(request: Request, category: str = Query(None), subtype: str = Query(None)):
    """Return emission factors; filter by category/subtype if provided."""
    # no auth needed for read
    rows = db.list_emission_factors()
    factors = [dict(r) for r in rows]
    if category:
        factors = [f for f in factors if f.get('category') == category]
    if subtype:
        factors = [f for f in factors if f.get('subtype') == subtype]
    return {"factors": factors}


@app.get('/api/metrics')
def api_get_metrics(request: Request):
    """Return computed user metrics for the current token/session user (quick JSON for UI refresh)."""
    api_user = _get_api_user(request)
    if not api_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    u = api_user
    try:
        metrics = get_user_metrics(u)
        return {"metrics": metrics}
    except Exception:
        return {"metrics": {}}

@app.post('/api/activities')
def api_add_activity(request: Request, category: str = Form(...), subtype: str = Form(None), co2_kg: float = Form(None), note: str = Form(None), quantity: float = Form(None), unit: str = Form(None)):
    api_user = _get_api_user(request)
    if not api_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    u = api_user

    # --- LOGIKA ZA CO2 (Uštede i Emisije) ---
    final_co2 = 0.0
    
    # 1. Prisili negativan predznak za ekološke tipove transporta
    # Čak i ako korisnik pošalje 0.192, mi spremamo -0.192 (ušteda)
    if category and category.lower() == 'transport':
        if quantity is None or quantity == 0:
            return {"error": "Transport activities require 'quantity' in kilometers (km)."}
        
        if subtype in ['Bicikl', 'Hodanje', 'Bicycle', 'Walk']:
            # Faktor 0.192 je prosječna ušteda po km u odnosu na automobil
            final_co2 = -abs(quantity * 0.192)
        elif co2_kg is not None:
            final_co2 = float(co2_kg)
    
    # 2. Za sve ostale kategorije, ako CO2 nije poslan, pokušaj izračunati preko faktora
    elif (co2_kg is None or co2_kg == 0) and quantity is not None:
        ef = db.get_emission_factor(category, subtype)
        if ef and ef.get('co2_kg_per_unit') is not None:
            final_co2 = round(quantity * float(ef.get('co2_kg_per_unit')), 3)
        else:
            return {"error": "No emission factor found; please provide co2_kg explicitly"}
    else:
        # Ako je korisnik ručno unio CO2, koristi tu vrijednost (zadrži predznak)
        final_co2 = float(co2_kg) if co2_kg is not None else 0.0

    # 3. Dodaj jedinicu ako nedostaje
    if not unit:
        unit = UNITS.get(category, '')

    try:
        # Spremanje u bazu - final_co2 sada ima ispravan minus za uštede
        aid = db.add_activity(u.get('id'), category, subtype, float(final_co2), note, quantity, unit)
        
        # Obavijesti druge dijelove aplikacije o promjeni (ako koristiš signale)
        return {"id": aid, "co2_kg": final_co2, "ok": True}
    except Exception as e:
        return {"error": str(e)}
# ---------- GPS Tracking APIs ----------
@app.get('/api/tracks')
def api_get_tracks(request: Request):
    api_user = _get_api_user(request)
    if not api_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    u = api_user
    try:
        rows = db.get_tracks_for_user(u.get('id'))
        tracks = [dict(r) for r in rows]
        return {"tracks": tracks}
    except Exception as e:
        return {"error": str(e)}


@app.get('/api/tracks/{track_id}')
def api_get_track(request: Request, track_id: int):
    api_user = _get_api_user(request)
    if not api_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    u = api_user
    try:
        with db.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, user_id, activity_type, name, started_at, ended_at, distance_km, created_at FROM gps_tracks WHERE id = ?", (track_id,))
            tr = cur.fetchone()
            if not tr:
                return {"error": "Track not found"}
            t = dict(tr) if not isinstance(tr, dict) else tr
            # check ownership or admin
            if t.get('user_id') != u.get('id') and u.get('user_type') != 'admin':
                return JSONResponse({"error": "Not authorized"}, status_code=403)
            pts = db.get_track_points(track_id)
            points = []
            for p in pts:
                try:
                    points.append(dict(p))
                except Exception:
                    points.append({'seq': p[0], 'lat': p[1], 'lon': p[2], 'timestamp': p[3], 'accuracy': p[4], 'speed': p[5]})
            return {"track": t, "points": points}
    except Exception as e:
        return {"error": str(e)}


@app.post('/api/tracks')
async def api_save_track(request: Request):
    api_user = _get_api_user(request)
    if not api_user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    u = api_user
    try:
        data = await request.json()
    except Exception:
        return {"error": "Invalid JSON"}

    name = data.get('name')
    activity_type = data.get('activity_type')
    started_at = data.get('started_at')
    ended_at = data.get('ended_at')
    try:
        distance_km = float(data.get('distance_km')) if data.get('distance_km') is not None else None
    except Exception:
        distance_km = None
    points = data.get('points') or []

    try:
        tid = db.add_track(u.get('id'), activity_type or 'walk', name=name, started_at=started_at, ended_at=ended_at, distance_km=distance_km)
        for i, p in enumerate(points):
            db.add_track_point(tid, i, float(p.get('lat')), float(p.get('lon')), p.get('timestamp'), p.get('accuracy'), p.get('speed'))
        return {"ok": True, "id": tid}
    except Exception as e:
        return {"error": str(e)}


@app.post('/api/activities/{activity_id}/delete')
def api_delete_activity(request: Request, activity_id: int):
    if 'user' not in request.session:
        return RedirectResponse('/login')
    username = request.session['user']
    user = db.get_user_by_username(username)
    if not user:
        return {"error": "User not found"}
    u = dict(user) if not isinstance(user, dict) else user

    # allow owner or admin to delete
    act = db.get_activity(activity_id)
    if not act:
        return {"error": "Activity not found"}
    owner_id = act['user_id']
    if owner_id != u.get('id') and not is_session_admin(request):
        return {"error": "Not authorized"}

    try:
        deleted = db.delete_activity(activity_id)
        return {"deleted": deleted}
    except Exception as e:
        return {"error": str(e)}


# ========== ADMIN API ENDPOINTS (for Android admin tools) ==========

@app.get('/api/admin/users')
def api_admin_get_users(request: Request, limit: int = Query(1000)):
    """Return all users (admin only)."""
    r = require_api_admin(request)
    if r:
        return r
    try:
        rows = db.get_all_users()
        users = []
        for row in rows:
            try:
                u = dict(row) if not isinstance(row, dict) else row
            except Exception:
                u = {'id': row[0], 'username': row[1], 'email': row[2], 'name': row[4] if len(row) > 4 else None, 'created_at': row[3] if len(row) > 3 else None, 'is_active': 1}
            users.append({
                'id': u.get('id'),
                'username': u.get('username'),
                'email': u.get('email'),
                'name': u.get('name'),
                'created_at': u.get('created_at'),
                'is_active': u.get('user_type') != 'disabled'
            })
        return {"users": users[:limit]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post('/api/admin/users')
async def api_admin_add_user(request: Request):
    """Add a new user (admin only)."""
    r = require_api_admin(request)
    if r:
        return r
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    
    try:
        username = data.get('username')
        email = data.get('email')
        name = data.get('name')
        password = data.get('password')
        is_active = data.get('is_active', True)
        
        if not username or not email or not password:
            return JSONResponse({"error": "Missing required fields: username, email, password"}, status_code=400)
        
        if db.get_user_by_username(username):
            return JSONResponse({"error": "Username already exists"}, status_code=400)
        
        pwd_hash = pwd_context.hash(password)
        user_type = 'admin' if data.get('user_type') == 'admin' else 'user'
        new_id = db.add_user(username=username, email=email, name=name, password_hash=pwd_hash, user_type=user_type)
        
        new_user = db.get_user(new_id)
        u = dict(new_user) if new_user else {}
        return {
            "id": new_id,
            "username": username,
            "email": email,
            "name": name,
            "created_at": u.get('created_at'),
            "is_active": is_active
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post('/api/admin/users/{user_id}')
async def api_admin_update_user(request: Request, user_id: int):
    """Update a user (admin only)."""
    r = require_api_admin(request)
    if r:
        return r
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    
    try:
        user = db.get_user(user_id)
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)
        
        updates = {}
        if 'username' in data:
            updates['username'] = data['username']
        if 'email' in data:
            updates['email'] = data['email']
        if 'name' in data:
            updates['name'] = data['name']
        if 'password' in data and data['password']:
            updates['password_hash'] = pwd_context.hash(data['password'])
        
        db.update_user(user_id, **updates)
        updated_user = db.get_user(user_id)
        u = dict(updated_user) if updated_user else {}
        return {
            "id": user_id,
            "username": u.get('username'),
            "email": u.get('email'),
            "name": u.get('name'),
            "created_at": u.get('created_at'),
            "is_active": u.get('user_type') != 'disabled'
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.delete('/api/admin/users/{user_id}')
def api_admin_delete_user(request: Request, user_id: int):
    """Delete a user (admin only)."""
    r = require_api_admin(request)
    if r:
        return r
    try:
        user = db.get_user(user_id)
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)
        
        u = dict(user) if not isinstance(user, dict) else user
        # Prevent deleting permanent admin account
        if u.get('permanent') and u.get('username') == 'admin':
            return JSONResponse({"error": "Cannot delete permanent admin account"}, status_code=403)
        
        db.delete_user(user_id)
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get('/api/admin/factors')
def api_admin_get_factors(request: Request):
    """Get all emission factors (admin only)."""
    r = require_api_admin(request)
    if r:
        return r
    try:
        rows = db.list_emission_factors()
        factors = []
        for row in rows:
            try:
                f = dict(row) if not isinstance(row, dict) else row
            except Exception:
                # Fallback for tuple: id, category, subtype, unit, co2_kg_per_unit, source, created_at
                f = {'id': row[0], 'category': row[1], 'subtype': row[2], 'unit': row[3], 'co2_kg_per_unit': row[4], 'source': row[5], 'created_at': row[6] if len(row) > 6 else None}
            factors.append(f)
        return {"factors": factors}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post('/api/admin/factors/{factor_id}')
async def api_admin_update_factor(request: Request, factor_id: int):
    """Update an emission factor (admin only)."""
    r = require_api_admin(request)
    if r:
        return r
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    
    try:
        factor_value = data.get('factor')
        if factor_value is None:
            return JSONResponse({"error": "Missing 'factor' value"}, status_code=400)
        
        # Update the emission factor
        updated = db.update_emission_factor(factor_id, co2_kg_per_unit=float(factor_value))
        return {"ok": True, "updated": updated}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get('/api/admin/tracks')
def api_admin_get_tracks(request: Request, limit: int = Query(1000)):
    """Get all GPS tracks (admin only)."""
    r = require_api_admin(request)
    if r:
        return r
    try:
        rows = db.get_all_tracks(limit=limit)
        tracks = []
        for row in rows:
            try:
                t = dict(row) if not isinstance(row, dict) else row
            except Exception:
                t = {'id': row[0], 'user_id': row[1], 'name': row[4], 'distance_km': row[7], 'created_at': row[8] if len(row) > 8 else None}
            tracks.append(t)
        return {"tracks": tracks}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.delete('/api/admin/tracks/{track_id}')
def api_admin_delete_track(request: Request, track_id: int):
    """Delete a GPS track (admin only)."""
    r = require_api_admin(request)
    if r:
        return r
    try:
        track = db.get_track(track_id)
        if not track:
            return JSONResponse({"error": "Track not found"}, status_code=404)
        
        db.delete_track(track_id)
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get('/api/admin/activities')
def api_admin_get_activities(request: Request, limit: int = Query(1000)):
    """Get all activities (admin only)."""
    r = require_api_admin(request)
    if r:
        return r
    try:
        rows = db.get_all_activities(limit=limit)
        activities = []
        for row in rows:
            try:
                a = dict(row) if not isinstance(row, dict) else row
            except Exception:
                a = {'id': row[0], 'user_id': row[1], 'category': row[3], 'subtype': row[4], 'co2_kg': row[5], 'quantity': row[6], 'unit': row[7], 'created_at': row[9] if len(row) > 9 else None}
            activities.append(a)
        return {"activities": activities}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.delete('/api/admin/activities/{activity_id}')
def api_admin_delete_activity(request: Request, activity_id: int):
    """Delete an activity (admin only)."""
    r = require_api_admin(request)
    if r:
        return r
    try:
        activity = db.get_activity(activity_id)
        if not activity:
            return JSONResponse({"error": "Activity not found"}, status_code=404)
        
        db.delete_activity(activity_id)
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

