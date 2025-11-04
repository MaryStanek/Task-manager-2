import os
import mysql.connector
from mysql.connector import Error

# Připojení k databázi
#pip install mysql-connector-python
#pip install fido2
def pripojeni_db():
 try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='1111',
            use_pure=True,
            database='spravce_ukolu'
            )
        if conn.is_connected():
            print("+ Připojení k databázi bylo úspěšné.")
            return conn
 except Error as e:
        print("!!! Chyba při připojování k databázi:")
        print(e)
        return None
    
def vytvoreni_tabulky():
  #Ověřit, že existuje tabulka "ukoly"
  try:
      connection = pripojeni_db()
      kursor = connection.cursor()
      kursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'spravce_ukolu' 
        AND table_name = 'ukoly';
        """)
      (pocet,) = kursor.fetchone()
      if pocet > 0:
          print("+ Tabulka 'ukoly' existuje.")
      else:
          print("! Tabulka 'ukoly' neexistuje — vytvářím tabulku 'ukoly'")
          #by se mel doprogramovat prikaz na vytvoreni tabulky
          #bude nový sql příkz
          kursor.execute("""
            create table ukoly (
            ID INT primary key auto_increment,
            Nazev Varchar(50) not null,
            Popis Varchar(50) not null,
            Stav Enum ('nezahajeno', 'probiha', 'hotovo') Default 'nezahajeno',
            Datum_vytvoreni datetime default current_timestamp
            );
            """)
      kursor.close
      connection.close
  except Error as e:
      print("!!! Chyba při kontrole tabulky:", e)
  return None

def pridat_ukol():    
  #nazev = input("Zadej název úkolu: ").strip()
  #popis = input("Zadej popis úkolu: ").strip()
  while True:
      nazev = input("Zadej název úkolu: ").strip()
      if nazev is None or nazev.strip() == "":
          print("! Název úkolu nesmí být prázdný.")
      else:
          break
  while True:
      popis = input("Zadej popis úkolu: ").strip()
      if popis is None or popis.strip() == "":
          print("! Popis úkolu nesmí být prázdný.")
      else:
          break
  connection = pripojeni_db()
  kursor = connection.cursor()
  # SQL příkaz pro vložení
  sql = """
          INSERT INTO ukoly (Nazev, Popis)
          VALUES (%s, %s);
          """
  data = (nazev, popis)
  kursor.execute(sql, data)
  #kursor.execute(sql)
  if kursor.rowcount > 0:
    print(f"+ Příkaz proběhl vloženo {kursor.rowcount} řádek/záznam.")
  else:
    print("! Nebyl vložen žádný řádek.")
  connection.commit()
  kursor.close
  connection.close
  return

def zobrazit_ukoly(zkracenyvystup=""):
  connection = pripojeni_db()
  if connection is None:
    return
  try:
      kursor = connection.cursor()
      # SQL dotaz: vybere jen "nezahajeno" nebo "probiha"
      kursor.execute("""
          SELECT ID, Nazev, Popis, Stav 
          FROM ukoly
          WHERE Stav IN ('nezahajeno', 'probiha')
          ORDER BY LENGTH(Nazev), Nazev;
      """)
      vysledky = kursor.fetchall()
      if len(vysledky) == 0:
          print("! Seznam úkolů je prázdný.")
      else:
          print("\nSeznam úkolů:")
          print("-" * 50)
          #delka = [0] * len(vysledky[0])  # jeden sloupec = jedna položka
          for row in vysledky:
              #spocitam si delku sloupku pro rozumnejsi zarovnani tabulky
              #for polozka in row:
              #  delka.append(len(str(polozka)))  # převedeme na string a uložíme délku
              #delka = [len(row[i]) for i in range(len(row))]
              #for i in range(len(str(row))):
              #      delka[i] = max(delka[i], len(str(row[i])))
              #vpsani tabulky
              if zkracenyvystup == "":
                print(f"ID: {row[0]} | Název: {row[1]} | Popis: {row[2]} | Stav: {row[3]}")
                #print(f"ID:{row[0]:<5} | Název: {row[1]:<50} | Popis: {row[2]:<50} | Stav: {row[3]:<10}")
                #print(f"ID:{row[0]:<delka[0]} | Název: {row[1]:<delka[1]} | Popis: {row[2]:<delka[2]} | Stav: {row[3]:<delka[3]}")
              else:
                 print(f"ID: {row[0]} | Název: {row[1]} | Stav: {row[3]}")
          print("-" * 50)
          #vraceni nalezenych ID pro moznosti update
          return [row[0] for row in vysledky]
  except Error as e:
      print("! Chyba při načítání úkolů:", e)
  finally:
      if 'cursor' in locals():
          kursor.close()
      if 'connection' in locals():
          connection.close()

def aktualizovat_ukol():
    while True:
        existujici_id = zobrazit_ukoly("zkracenyvystup")
        if not existujici_id:
            print("! Nenalezeny žádné úkoly:")
            return  # pokud nejsou žádné úkoly, funkce končí
        try:
            vybrane_id = int(input("Zadej ID úkolu, který chceš aktualizovat: ").strip())
            if vybrane_id not in existujici_id:
                print("Zadané ID neexistuje, zkus to znovu.")
                continue
        except ValueError:
            print("Prosím zadej platné číslo ID.")
            continue
        # výběr nového stavu
        while True:
            print("Nový stav úkolu:")
            print("1. Probíhá")
            print("2. Hotovo")
            volba = input("Zadej číslo volby: ").strip()
            if volba == "1":
                novy_stav = "probiha"
                break
            elif volba == "2":
                novy_stav = "hotovo"
                break
            else:
                print("Neplatná volba, zkus to znovu.")
        # aktualizace v DB
        connection = pripojeni_db()
        if connection is None:
            return
        try:
            cursor = connection.cursor()
            sql = "UPDATE ukoly SET Stav = %s WHERE ID = %s"
            data = (novy_stav, vybrane_id)
            cursor.execute(sql, data)
            connection.commit()
            print(f"Úkol s ID {vybrane_id} byl aktualizován na stav '{novy_stav}'.")
        except Error as e:
            print("! Chyba při aktualizaci úkolu:", e)
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
        break  # po úspěšné aktualizaci ukončíme cyklus

def odstranit_ukol():
    while True:
        existujici_id = zobrazit_ukoly()
        if not existujici_id:
            return  # pokud nejsou žádné úkoly, funkce končí
        try:
            vybrane_id = int(input("Zadej ID úkolu, který chceš odstranit: ").strip())
            if vybrane_id not in existujici_id:
                print("Zadané ID neexistuje, zkus to znovu.")
                continue
        except ValueError:
            print("Prosím zadej platné číslo ID.")
            continue
        # potvrzení smazání
        potvrzeni = input(f"Opravdu chceš odstranit úkol s ID {vybrane_id}? (ano/ne): ").strip().lower()
        if potvrzeni != "ano":
            print("Smazání zrušeno.")
            return
        # smazání v DB
        connection = pripojeni_db()
        if connection is None:
            return
        try:
            cursor = connection.cursor()
            sql = "DELETE FROM ukoly WHERE ID = %s"
            data = (vybrane_id,)
            cursor.execute(sql, data)
            connection.commit()
            print(f"Úkol s ID {vybrane_id} byl úspěšně odstraněn.")
        except Error as e:
            print("Chyba při mazání úkolu:", e)
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
        break  # po úspěšném smazání ukončíme cyklus

#  os.system('cls')
#priprava programu
programbezi=True
seznamukolu = {}

#nejprve provedeme kontrolu tabulky
vytvoreni_tabulky()

#Hlavni smycka
while programbezi==True:
  #programbezi=True

  ##Seznam úkolů string, pole
  hlavnimenu = ["1. Pridat novy ukol", "2. Zobrazit vsechny ukoly", "3. Aktualizovat úkol", "4. Odstranit ukol", "5. Konec programu"]
  #seznam úkolů databáze, který můj program spravuje

  ##Tady si vypíšu proměnnou úkoly
  print ("\nSpravce ukolu - Hlavni menu:")
  print ('\n'.join(hlavnimenu))

  # Uživatelský vstup uložený v proměnné jmeno
  zvoleny_ukol = input("Vyberte možnost (1-5): ")

  #vyhodnocení zvolené volby(očekává se int. 1-4)
  if zvoleny_ukol == "1":
    print("Vybraná volba: 1. Pridat novy ukol")
    pridat_ukol()
  elif zvoleny_ukol == "2":
    print("Vybraná volba: 2. Zobrazit vsechny ukoly")
    zobrazit_ukoly()
  elif zvoleny_ukol == "3":
    print("Vybraná volba: 3. Aktualizovat úkol")
    aktualizovat_ukol()
  elif zvoleny_ukol == "4":
    print("Vybraná volba: 4. Odstranit ukol")
    odstranit_ukol()
  elif zvoleny_ukol == "5":
    print("Vybraná volba: 5. Konec programu")
    programbezi=False
    #break   
  else:
    print("Neplatná volba. Zadejte volbu prosim znovu.")

print("Konec programu")
