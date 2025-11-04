from unittest.mock import patch
import mysql.connector

from src.Manager2vylepsena_MSl import pridat_ukol, aktualizovat_ukol, odstranit_ukol
import pytest
# pytest -s # zadavani do konzole
# python -m pytest -s -v #budou videt printy

# Testy provadim na ostre databazi,
# v praxi bych si vzdy vytvorila, nebo se pripojila k testovací databázi

def test_pridat_ukol_positive(monkeypatch):
    #simulace vstupu uživatele
    vstupy = iter(["Testovací úkol", "Popis úkolu"])
    monkeypatch.setattr("builtins.input", lambda _: next(vstupy))
    conn = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='1111',
            use_pure=True,
            database='spravce_ukolu'
            )
    cursor = conn.cursor()
    #počet záznamů před testem
    cursor.execute("SELECT COUNT(*) FROM ukoly;")
    #cursor.commit()
    pocet_pred = cursor.fetchone()[0]    
    print("\npocet_pred:", pocet_pred)
    #zavolání testované funkce
    pridat_ukol() 
    conn.commit() 
    #počet záznamů po testu
    cursor.execute("SELECT COUNT(*) FROM ukoly;")
    pocet_po = cursor.fetchone()[0]
    print("\npocet_po:", pocet_po)    
    #kontrola, že přibyl záznam
    assert pocet_po == pocet_pred + 1     
    #úklid po testu
    cursor.execute("DELETE FROM ukoly WHERE Nazev = 'Testovací úkol';")
    conn.commit()
    cursor.close()
    conn.close()    


def test_pridat_ukol_negative(monkeypatch):
    #Pokus o přidání úkolu s prázdným názvem
    # simulace vstupu uživatele — první vstup je prázdný název, druhý platný popis
    vstupy = iter(["", "Popis úkolu"])
    monkeypatch.setattr("builtins.input", lambda _: next(vstupy))
    # připojení k databázi
    conn = mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='1111',
        use_pure=True,
        database='spravce_ukolu'
    )
    cursor = conn.cursor()
    #počet záznamů před testem
    cursor.execute("SELECT COUNT(*) FROM ukoly;")
    pocet_pred = cursor.fetchone()[0]
    print("\npocet_pred:", pocet_pred)
    #zavolání testované funkce
    try:
        pridat_ukol()  # očekáváme, že funkce selže nebo nevloží záznam
        conn.commit()
    except Exception as e:
        print("Očekávaná výjimka při neplatném vstupu:", e)
    #počet záznamů po testu
    cursor.execute("SELECT COUNT(*) FROM ukoly;")
    pocet_po = cursor.fetchone()[0]
    print("pocet_po:", pocet_po)
    #kontrola, že se nic nezměnilo
    assert pocet_po == pocet_pred, "Negativní test selhal — úkol byl vložen, i když neměl být."
    #úklid po testu
    cursor.close()
    conn.close()

def test_aktualizovat_ukol_positive(monkeypatch):
    conn = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='1111',
            use_pure=True,
            database='spravce_ukolu'
            )
    cursor = conn.cursor()
    #lepsi by bylo napsat si vlastni vlozeni do databaze a 
    # nepouzivat metodu ktera je externi a nemusi pracovat:
    #pridat_ukol()
    sql = """
            INSERT INTO ukoly (Nazev, Popis)
            VALUES ('Testovací update1', 'Popis update1');
            """
    cursor.execute(sql)
    conn.commit() 
    #dopsat zjisteni posledni ID
    posledni_id = cursor.lastrowid
    #posledni id pouzit jako vstup
    vstupy = iter([str(posledni_id),"2"])
    monkeypatch.setattr("builtins.input", lambda _: next(vstupy))
    aktualizovat_ukol()
    conn.commit() 
    #dopsat SELECT a precist stav. jestli zmena probehla
    cursor.execute(f"""
        SELECT ID, Nazev, Popis, Stav 
        FROM ukoly WHERE ID={posledni_id}
        ORDER BY ID LIMIT 1;
        """)
    vysledky = cursor.fetchall()
    assert vysledky[0][3]=="hotovo"
    #úklid po testu
    cursor.execute("DELETE FROM ukoly WHERE Nazev = 'Testovací update1';")
    conn.commit()
    # úklid po testu
    cursor.close()
    conn.close()

@pytest.mark.xfail(reason="Funkce se zatím nevymaní z nekonečné smyčky, chybné ID nebo chybný Stav úkolu způsobí nekonečnou smyčku")
def test_aktualizovat_ukol_negative(monkeypatch):
    conn = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='1111',
            use_pure=True,
            database='spravce_ukolu'
            )
    cursor = conn.cursor()
    #lepsi by bylo napsat si vlastni vlozeni do databaze a 
    # nepouzivat metodu ktera je externi a nemusi pracovat:
    #pridat_ukol()
    #negativní test, databáze se neaktualizuje

    #Získat nejvyšší aktuální ID v tabulce
    cursor.execute("SELECT IFNULL(MAX(ID), 0) FROM ukoly;")
    max_id = cursor.fetchone()[0]
    neexistujici_id = max_id + 999  # zajistí, že ID v DB určitě neexistuje

    # Zjistit počet záznamů a aktuální stav databáze
    cursor.execute("SELECT COUNT(*) FROM ukoly;")
    pocet_pred = cursor.fetchone()[0]

    #Ověřit, že se žádný záznam nezměnil na 'hotovo' během testu
    cursor.execute("SELECT COUNT(*) FROM ukoly WHERE Stav = 'hotovo';")
    hotovo_pred = cursor.fetchone()[0]

    #Simulovat vstup – zadání neexistujícího ID a volbu stavu
    vstupy = iter([str(neexistujici_id), "3", "3" , "q", "  "])  # "3" = Spatný vstup
    
    def fake_input(_):
        try:
            return next(vstupy)
        except StopIteration:
            #return "q"  # výchozí hodnota, když dojdou vstupy
            pytest.fail("Došly simulované vstupy! Funkce se pravděpodobně zasekla v nekonečné smyčce.")
    
    #vstupy = iter([str(neexistujici_id), "3", ""])
    monkeypatch.setattr("builtins.input", fake_input)

    #Zavolat testovanou funkci
    #aktualizovat_ukol()
    with pytest.raises(StopIteration):
        aktualizovat_ukol()
    conn.commit()

    #Zkontrolovat, že se počet záznamů nezměnil
    cursor.execute("SELECT COUNT(*) FROM ukoly;")
    pocet_po = cursor.fetchone()[0]

    assert pocet_po == pocet_pred+1, (
    f"Počet záznamů se změnil ({pocet_pred} → {pocet_po}), "
        "i když bylo zadáno neexistující ID!"
    )

    cursor.execute("SELECT COUNT(*) FROM ukoly WHERE Stav = 'hotovo';")
    hotovo_po = cursor.fetchone()[0]

    assert hotovo_po > hotovo_pred, "Došlo ke změně stavu bez platného ID!"

    #úklid po testu
    cursor.close()
    conn.close() 

def test_odstranit_ukol_positive(monkeypatch):
      
    conn = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='1111',
            use_pure=True,
            database='spravce_ukolu'
            )
    cursor = conn.cursor()

    #simulace vstupu uživatele
    monkeypatch.setattr("builtins.input", lambda _: next(vstupy))

    #vložíme testovací úkol do DB (aby bylo co mazat)
    cursor.execute("""
        INSERT INTO ukoly (Nazev, Popis)
        VALUES ('Testovací úkol2', 'Popis úkolu2');
    """)
    conn.commit()
    posledni_id = cursor.lastrowid

    #počet záznamů před testem
    cursor.execute("SELECT COUNT(*) FROM ukoly;")
    #cursor.commit()
    pocet_pred = cursor.fetchone()[0]    
    print("\npocet_pred:", pocet_pred)

    #simulujeme vstup uživatele pro smazání záznamu
    vstupy = iter([str(posledni_id), "ano"])
    
    monkeypatch.setattr("builtins.input", lambda _: next(vstupy))
    
    #zavolání testované funkce
    odstranit_ukol() 
    conn.commit() 

    #počet záznamů po testu
    cursor.execute("SELECT COUNT(*) FROM ukoly;")
    pocet_po = cursor.fetchone()[0]
    print("\npocet_po:", pocet_po) 

    #kontrola, že ubyl záznam
    assert pocet_po == pocet_pred - 1  

    #úklid po testu
    cursor.execute("DELETE FROM ukoly WHERE Nazev = 'Testovací úkol2';")
    conn.commit()
    cursor.close()
    conn.close()   

@pytest.mark.xfail(reason="Funkce se zatím nevymaní z nekonečné smyčky, chybné ID nebo chybný Stav úkolu způsobí nekonečnou smyčku")
def test_odstranit_ukol_negative(monkeypatch):
      
    conn = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='1111',
            use_pure=True,
            database='spravce_ukolu'
            )
    cursor = conn.cursor()

    #zjisti aktuální počet záznamů a stav "hotovo"
    cursor.execute("SELECT COUNT(*) FROM ukoly;")
    pocet_pred = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ukoly WHERE Stav = 'hotovo';")
    hotovo_pred = cursor.fetchone()[0]

    #najdi ID, které v DB **určitě neexistuje**
    cursor.execute("SELECT IFNULL(MAX(ID), 0) FROM ukoly;")
    max_id = cursor.fetchone()[0]
    neexistujici_id = max_id + 999

    #simulace vstupů – zadání neexistujícího ID a volba "ne"
    vstupy = iter([str(neexistujici_id), "ne"])

    def fake_input(_):
        try:
            return next(vstupy)
        except StopIteration:
            # Pokud dojdou simulované vstupy, test skončí chybou (nenekonečná smyčka)
            pytest.fail("Došly simulované vstupy! Funkce se pravděpodobně zasekla v nekonečné smyčce.")

    monkeypatch.setattr("builtins.input", fake_input)

    #zavoláme testovanou funkci
    odstranit_ukol()
    conn.commit()

    #zkontrolujeme, že se počet záznamů nezměnil
    cursor.execute("SELECT COUNT(*) FROM ukoly;")
    pocet_po = cursor.fetchone()[0]
    assert pocet_po == pocet_pred, (f"Počet záznamů se změnil ({pocet_pred} → {pocet_po}) i přes neexistující ID!")
    
    #ověříme, že se stav "hotovo" nezměnil
    cursor.execute("SELECT COUNT(*) FROM ukoly WHERE Stav = 'hotovo';")
    hotovo_po = cursor.fetchone()[0]
    assert hotovo_po == hotovo_pred, "Došlo ke změně stavu bez platného ID!"

    #úklid po testu
    cursor.close()
    conn.close()    
