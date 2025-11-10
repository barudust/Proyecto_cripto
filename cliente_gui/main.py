# main.py
# Menú integrador: registrar usuario (genera claves), cifrar (crea ZIP), descifrar
import os, sys
import claves, cifrar, descifrar

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def pause():
    input("Presiona ENTER para continuar...")

def menu():
    while True:
        clear()
        print("=== PROYECTO: Protección de Documentos (Cliente local) ===")
        print("1) Registrar usuario y generar claves")
        print("2) Cifrar y empaquetar (ZIP) [firma incluida, cifrada con DEK]")
        print("3) Descifrar y verificar firma")
        print("4) Salir")
        opt = input("Opción: ").strip()
        if opt == "1":
            try:
                claves.generate_and_register()
            except Exception as e:
                print("Error:", e)
            pause()
        elif opt == "2":
            try:
                cifrar.main()
            except Exception as e:
                print("Error durante cifrado:", e)
            pause()
        elif opt == "3":
            try:
                descifrar.main()
            except Exception as e:
                print("Error durante descifrado:", e)
            pause()
        elif opt == "4":
            print("Saliendo...")
            sys.exit(0)
        else:
            print("Opción inválida.")
            pause()

if __name__ == "__main__":
    menu()
