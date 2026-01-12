# **SDIP \- System Dynamicznej Informacji Pasażerskiej**

System umożliwiający zarządzanie i wyświetlanie tablic odjazdów oraz generowanie automatycznych zapowiedzi głosowych.

## **Wymagania wstępne**

Przed przystąpieniem do instalacji upewnij się, że na Twoim urządzeniu zainstalowano:

* **Python 3.x** ([pobierz](https://www.python.org/downloads/))  
* **Node.js i npm** ([pobierz](https://nodejs.org/en/download))  
* **PostgreSQL** ([pobierz](https://www.postgresql.org/download/)) wraz z narzędziem **pgAdmin**  
* **Git** ([pobierz](https://git-scm.com/install/))

## **Instalacja**

### **1\. Pobranie kodu źródłowego**

Sklonuj repozytorium na dysk lokalny:

git clone \[https://github.com/gajpawel/SDIP-POLSL\](https://github.com/gajpawel/SDIP-POLSL)  
cd SDIP-POLSL

### **2\. Konfiguracja Backend (Serwer)**

Przejdź do folderu backend i zainstaluj wymagane biblioteki:

cd backend  
pip install fastapi uvicorn\[standard\] sqlalchemy psycopg2-binary passlib\[bcrypt\] python-jose elevenlabs python-dotenv

Utwórz w folderze backend plik .env i uzupełnij go danymi:

ELEVENLABS\_API\_KEY=twoj\_klucz\_api  
SQLALCHEMY\_DATABASE\_URL=postgresql://\<USER\>:\<PASSWORD\>@\<HOST\>:\<PORT\>/\<DATABASE\>

*Klucz API ElevenLabs uzyskasz na [elevenlabs.io](https://elevenlabs.io/app/developers/api-keys).*

### **3\. Konfiguracja Bazy Danych**

1. Uruchom serwer PostgreSQL i utwórz nową bazę danych.  
2. Zaimportuj schemat tabel za pomocą zapytania SQL z pliku data/sdip.sql.  
3. Wczytaj dane z plików .csv znajdujących się w folderze data (nazwa pliku odpowiada nazwie tabeli).  
4. (Opcjonalnie) Zaimportuj dane testowe z folderu data/sample.

### **4\. Konfiguracja Frontend (Klient)**

Przejdź do folderu frontend i zainstaluj zależności:

cd ../frontend  
npm install

## **Uruchomienie systemu**

System wymaga jednoczesnego działania dwóch procesów:

**Uruchomienie Backendu:**

\# W folderze /backend  
uvicorn main:app \--host 0.0.0.0 \--port 8000

**Uruchomienie Frontendu:**

\# W folderze /frontend  
npm run dev \-- \--host

## **Pierwsze logowanie**

Po uruchomieniu przejdź pod adres wskazany przez narzędzie Vite.

* **Login:** admin  
* **Hasło:** admin

**Uwaga:** Ze względów bezpieczeństwa należy niezwłocznie zmienić dane logowania administratora po pierwszym uruchomieniu.