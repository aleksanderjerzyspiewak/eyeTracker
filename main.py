import keyboard
from collections import Counter
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
from keyboardOwn import get_keyboard_data
from documentBuilder import StringTable
import sugestions

# klawisze funkcyjne podmieniając w s a d c na wyplute przez kamerke
# program zachowa swoje działanie
key_map = {
    'w': 'up',
    's': 'down',
    'a': 'left',
    'd': 'right',
    'c': 'center',
}

# ------------------------------------------------------------------
# deklaracje podstawowych wartości
# ------------------------------------------------------------------

# tabela z document builder klasa odpowiedzialna za budowe
# tekstu z literek i pracy nad nim
table = StringTable()
# bufor przechowuje pewną ilość wszystkich ostatnich ruchów
buffer = []
# przechowuje ruchy, które wyszły z bufora
string_buffer = []
# czułość bufora czyli ile ostatnich ruchów przechowuje
# poprawność zależy od komputera złozonosci, powinien być ustawiany
# w trakcie strojenia programu
state_input = 2000
# przechowuje aktualny adres obrazu klawiatury
_, actual_image = get_keyboard_data([])
# tablica przechowująca podpowiedzi
suggestions = []
# ostatni wybrany kierunek
last = 'center'


# funkcja wpisująca wybraną podpowiedź
def suggest_to_panel(i):
    n = int(i[3])
    word_array = sugestions.last_three_words_from_last_sentence_v4(table.print_current())
    last_string = word_array[-1]
    how_many = len(last_string)
    for i in range(how_many):
        table.delete_in_move()
    if n-1 < len(suggestions):
        table.insert_to_current(suggestions[n-1])
# ------------------------------------------------------------------
# TK inter czyli gui
# ------------------------------------------------------------------


# update zdięcia w tkinter w istniejącym niżej zadeklarowanym widgecie
def update_image(image_path_loc):
    global photo  # Globalna zmienna, aby zdjęcie nie zostało usunięte przez Python garbage collector
    image = Image.open(image_path_loc)
    photo = ImageTk.PhotoImage(image)
    label.config(image=photo)
    label.image = photo


# update textu w tkinter w istniejącym niżej zadeklarowanym widgecie
def update_text_display():
    text_display.config(state='normal')

    actual_string = table.current_index
    actual_char = table.move_index

    text_display.delete('1.0', tk.END)  # Usuń bieżącą zawartość
    for strv in table.strings:
        text_display.insert(tk.END, strv+'\n')  # Wstaw bieżący tekst

    cursor_position = f"{actual_string + 1}.{actual_char}"
    text_display.mark_names()
    text_display.mark_set(tk.INSERT, cursor_position)
    text_display.see(tk.INSERT)


# blokowanie klawiatury na czas testowania
def block_key_press(event):
    none = event
    print(none)
    return "break"


# update widget do podpowiedzi
def update_string_list(strings):
    string_list_display.delete('1.0', tk.END)
    for i, s in enumerate(strings, 1):
        string_list_display.insert(tk.END, f"{i} {s or 'none'}\n")


# instrukcja wyswietlana na stałe jako widget oraz ostatni kierunek
instruction = "W-góra\nS-dół\nA-Lewo\nD-Prawo\nC-center\nQ-wyjście\n"
instruction += "\nKlawisz należy przytrzymać \naż do wykonania działania, "
instruction += "\nwsad nie działa jeżeli \naktualnie nie jest center"

# Inicjalizacja głównego okna
root = tk.Tk()
root.geometry('1600x900')  # Ustawienie rozmiaru okna

# Konfiguracja wyświetlacza tekstu
custom_font = font.Font(family='Helvetica', size=14, weight='bold')  # Tworzenie obiektu czcionki
text_display = tk.Text(root, font=custom_font)  # Stosowanie czcionki
text_display.place(x=0, y=0, width=600, height=900)
text_display.focus_set()
text_display.bind("<Key>", block_key_press)

# Miejsce na inne widgety (może być puste)
placeholder = tk.Label(root, text="", bg='grey')
placeholder.place(x=1400, y=0, width=200, height=900)

# Konfiguracja wyświetlacza instrukcji
instructions_display = tk.Text(root)
instructions_display.place(x=600, y=0, width=300, height=300)

# Konfiguracja wyświetlacza listy ciągów
string_list_display = tk.Text(root)
string_list_display.place(x=900, y=0, width=500, height=300)

# Etykieta do wyświetlania obrazów
label = tk.Label(root, borderwidth=2, relief="groove")
label.place(x=600, y=300, width=800, height=600)

# ustawienie początkowych wartosci dla zdj i instrukcji
update_image(actual_image)
instructions_display.insert(tk.END, f"Last: {last}\n\n{instruction}")

while True:
    # tkinter wymaga
    root.update()
    # jeżeli bufor ma więcej elementów niz ustawione w czułości
    if len(buffer) > state_input:
        #s sprawdza jaki był najczęściej
        most_frequent_key = Counter(buffer).most_common(1)[0][0]
        # if zapewnia że po każdym kierunku user musi wrócić do center
        if last == 'center' and most_frequent_key != 'center':
            # dodaje kierunek do tablicy kierunków
            string_buffer.append(most_frequent_key)
            # zeruje bufor
            buffer = []
            # zmienia ostatni by zagwarantować powrot do center
            last = most_frequent_key

            # pobiera literkę i adres, jeżeli nie ma zwraca none
            letter, image_path = get_keyboard_data(string_buffer)
            if letter == 'Error0':
                # gdy za długa ścieżka lub nieprawidłowy string
                print(image_path)
            else:
                # wszystkie znaki funkcyjne niebędące literami
                if letter != 'none':
                    if letter == 'space':
                        table.insert_to_current(' ')
                    elif letter == 'backspace':
                        table.delete_in_move()
                    elif letter == 'quote':
                        table.insert_to_current('"')
                    elif letter == 'left':
                        table.go_left()
                    elif letter == 'right':
                        table.go_right()
                    elif letter == 'up':
                        table.go_up()
                    elif letter == 'down':
                        table.go_down()
                    elif letter == 'enter':
                        table.enter_string()
                    elif letter == 'deleteAll':
                        table.delete_All()
                    elif letter == 'delete':
                        table.delete_current()
                    elif letter == 'print':
                        table.save_to_document()
                        # po zapisie do lokalnego folderu koniec progeramu
                        break
                    # podpowiedzi i wcześniejsza funkcja
                    elif letter in ('pod1', 'pod2', 'pod3', 'pod4'):
                        suggest_to_panel(letter)
                    else:
                        #jeżeli literka to nie none i nie znak funkcyjny dodaje ją do budowanego projektu
                        table.insert_to_current(letter)
                    # gdy wpiszemy literke zerujemy tablice kierunków
                    string_buffer = []

                    # pobieramy aktualny obraz
                    _, actual_image = get_keyboard_data([])
                if image_path != 'none':
                    # jeżeli ścieżka istnieje rysujemy ją
                    actual_image = image_path

        elif most_frequent_key == 'center':
            buffer = []
            last = most_frequent_key
            # jeżeli ostatni to center i obecnie znowu
            # zerujemy wszystko daje to nieskończony czas
            # na zastanawianie się
        else:
            buffer = []
            # gdy cały czas patrzymy w jednym kierunku ochrona przed spaem

        # rysowanie na tkinter pobranych wcześniej danych
        update_image(actual_image)
        update_text_display()
        instructions_display.delete('1.0', tk.END)
        instructions_display.insert(tk.END, f"Last: {last}\n\n{instruction}")

        # podpowiedzi
        input_text = sugestions.last_three_words_from_last_sentence_v4(table.print_current())
        if len(input_text) == 1:
            suggestions = sugestions.get_suggestions(input_text[0])
        if len(input_text) == 2:
            suggestions = sugestions.get_suggestions(input_text[1], input_text[0])
            if input_text[1] == '':
                sugestions.add_or_update_word(input_text[0])
        if len(input_text) == 3:
            suggestions = sugestions.get_suggestions(input_text[2], input_text[1], input_text[0])
            if input_text[2] == '':
                sugestions.add_or_update_first_degree_connection(input_text[1], input_text[0])

        suggestions = suggestions[:4]
        update_string_list(suggestions)

# ##################################################!!!!!!!!!!!!
# ważne
# tutaj tak naprwdę podmieniasz na funkcję czytającą kierunki z kamery
# jeżeli wcześniej ustawiłeś key map będzie działać
    for key in key_map:
        if keyboard.is_pressed(key):
            buffer.append(key_map[key])

# exit z programu jako q
    if keyboard.is_pressed('q'):
        print("End")
        exit()

# konec tkinter
root.mainloop()
