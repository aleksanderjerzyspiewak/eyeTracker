import os
import sys
import sqlite3

def connect_db():
    return sqlite3.connect('word_suggestions.db')

def add_or_update_word(word):
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT count FROM words WHERE word = ?', (word,))
    result = c.fetchone()
    if result:
        # Jeśli wyraz istnieje, zwiększamy licznik
        new_count = result[0] + 1
        c.execute('UPDATE words SET count = ? WHERE word = ?', (new_count, word))
    else:
        # Jeśli wyraz nie istnieje, dodajemy go z licznikiem 0
        c.execute('INSERT INTO words (word, count) VALUES (?, 1)', (word,))
    conn.commit()
    conn.close()

def add_or_update_first_degree_connection(prev_word, next_word):
    conn = connect_db()
    c = conn.cursor()
    # Dodajemy lub aktualizujemy wyrazy
    add_or_update_word(prev_word)
    add_or_update_word(next_word)
    # Pobieramy ich ID
    c.execute('SELECT id FROM words WHERE word=?', (prev_word,))
    prev_word_id = c.fetchone()[0]
    c.execute('SELECT id FROM words WHERE word=?', (next_word,))
    next_word_id = c.fetchone()[0]
    # Sprawdzamy, czy połączenie już istnieje
    c.execute('SELECT count FROM first_degree_connections WHERE prev_word_id=? AND next_word_id=?', (prev_word_id, next_word_id))
    result = c.fetchone()
    if result:
        # Jeśli połączenie istnieje, zwiększamy licznik
        new_count = result[0] + 1
        c.execute('UPDATE first_degree_connections SET count = ? WHERE prev_word_id = ? AND next_word_id = ?', (new_count, prev_word_id, next_word_id))
    else:
        # Jeśli połączenie nie istnieje, dodajemy je z licznikiem 0
        c.execute('INSERT INTO first_degree_connections (prev_word_id, next_word_id, count) VALUES (?, ?, 1)', (prev_word_id, next_word_id))
    conn.commit()
    conn.close()

def add_or_update_third_degree_connection(first_word, second_word, following_word):
    conn = connect_db()
    c = conn.cursor()

    # Dodajemy lub aktualizujemy wyrazy
    add_or_update_word(first_word)
    add_or_update_word(second_word)
    add_or_update_word(following_word)

    # Pobieramy ID wyrazów
    c.execute('SELECT id FROM words WHERE word=?', (first_word,))
    first_word_id = c.fetchone()[0]
    # print(first_word_id)
    c.execute('SELECT id FROM words WHERE word=?', (second_word,))
    second_word_id = c.fetchone()[0]
    # print(second_word_id)
    c.execute('SELECT id FROM words WHERE word=?', (following_word,))
    following_word_id = c.fetchone()[0]
    # print(following_word_id)

    # Pobieramy ID połączenia pierwszego stopnia na podstawie pierwszego i drugiego wyrazu
    c.execute('SELECT id FROM first_degree_connections WHERE prev_word_id=? AND next_word_id=?',
              (first_word_id, second_word_id))
    result = c.fetchone()
    if not result:
        # Jeśli nie ma takiego połączenia, najpierw je tworzymy
        c.execute('INSERT INTO first_degree_connections (prev_word_id, next_word_id, count) VALUES (?, ?, 1)',
                  (first_word_id, second_word_id))
        first_degree_id = c.lastrowid
    else:
        first_degree_id = result[0]

    # Sprawdzamy, czy połączenie trzeciego stopnia już istnieje
    c.execute('SELECT count FROM third_degree_connections WHERE first_degree_id=? AND following_word_id=?',
              (first_degree_id, following_word_id))
    result = c.fetchone()
    if result:
        # Jeśli połączenie istnieje, zwiększamy licznik
        new_count = result[0] + 1
        c.execute('UPDATE third_degree_connections SET count = ? WHERE first_degree_id = ? AND following_word_id = ?',
                  (new_count, first_degree_id, following_word_id))
    else:
        # Jeśli połączenie nie istnieje, dodajemy je z licznikiem 0
        c.execute('INSERT INTO third_degree_connections (first_degree_id, following_word_id, count) VALUES (?, ?, 1)',
                  (first_degree_id, following_word_id))
    conn.commit()
    conn.close()
def last_three_words_from_last_sentence_v4(s: str) -> list:
    # Split the input string into sentences by '.'
    sentences = s.split('.')
    # Check if the string ends with a space and adjust the behavior
    ends_with_space = s.endswith(' ')
    # Filter out empty sentences and strip whitespace
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    # Check if there are any sentences left
    if not sentences:
        return [""]
    # Take the last sentence
    last_sentence = sentences[-1]
    # Split the last sentence into words
    words = last_sentence.split()
    # If the string ends with a space, add an empty string to the result
    if ends_with_space and words:
        words.append("")
    # Return the last three words (considering the potential empty string addition), if there are less than three, return them all
    return words[-3:] if len(words) >= 3 else words


def get_suggestions(word=None, prev_word=None, prev_prev_word=None, min_suggestions_count=16):
    conn = connect_db()
    c = conn.cursor()
    suggestions_set = set()  # Zmiana na set, aby uniknąć duplikatów

    # Pierwotne zapytanie w zależności od dostępnych słów
    primary_queries = []
    if word == "" and not prev_word and not prev_prev_word:
        primary_queries.append(('SELECT word FROM words ORDER BY count DESC', ()))
    if word:
        primary_queries.append(('SELECT word FROM words WHERE word LIKE ? ORDER BY count DESC', (word + '%',)))
    if prev_word:
        primary_queries.append(('''SELECT w.word FROM first_degree_connections fdc
                                    JOIN words w ON fdc.next_word_id = w.id
                                    JOIN words pw ON fdc.prev_word_id = pw.id
                                    WHERE pw.word = ?
                                    ORDER BY fdc.count DESC''', (prev_word,)))
    if prev_word and word:
        primary_queries.append(('''SELECT w.word FROM first_degree_connections fdc
                                    JOIN words w ON fdc.next_word_id = w.id
                                    JOIN words pw ON fdc.prev_word_id = pw.id
                                    WHERE pw.word = ? AND w.word LIKE ?
                                    ORDER BY fdc.count DESC''', (prev_word, word + '%')))
    if prev_prev_word and prev_word:
        primary_queries.append(('''SELECT w.word FROM third_degree_connections tdc
                                    JOIN first_degree_connections fdc ON tdc.first_degree_id = fdc.id
                                    JOIN words w ON tdc.following_word_id = w.id
                                    JOIN words pw1 ON fdc.prev_word_id = pw1.id
                                    JOIN words pw2 ON fdc.next_word_id = pw2.id
                                    WHERE pw1.word = ? AND pw2.word = ? AND w.word LIKE ?
                                    ORDER BY tdc.count DESC''', (prev_prev_word, prev_word, word + '%')))

    # Wykonanie zapytań i uzupełnienie sugestii
    for query, params in primary_queries:
        if len(suggestions_set) < min_suggestions_count:
            c.execute(query, params)
            # Usuwanie kropek z wyrazów, pomijanie pustych wartości i dodawanie do zbioru, aby uniknąć duplikatów
            suggestions_set.update([row[0].replace('.', '') for row in c.fetchall() if row[0].replace('.', '')])

            # Przerwanie pętli, jeśli osiągnięto minimalną liczbę sugestii
            if len(suggestions_set) >= min_suggestions_count:
                break

    conn.close()
    # Konwersja na listę i ograniczenie do min_suggestions_count
    return list(suggestions_set)[:min_suggestions_count]



def interactive_prompt():
    test_inputs = [
        "",
        "go",
        "called ",
        "the lig",
        "and the ",
        "in the mi",
        "main libe lich null popopo. rose in the mi",
        "main libe lich null popopo. rose in the ",
        "with my ",
        "with my mot",
        "pan",
        "i like ",
        "I like pan",
        "the "
    ]

    test_outputs_v4 = [last_three_words_from_last_sentence_v4(input_text) for input_text in test_inputs]

    for input_text in test_outputs_v4:
        suggestions=[]
        if len(input_text)==1:
            suggestions=get_suggestions(input_text[0])
        if len(input_text) == 2:
            suggestions = get_suggestions(input_text[1], input_text[0])
            if input_text[1] == '':
                add_or_update_word(input_text[0])
        if len(input_text) == 3:
            suggestions = get_suggestions(input_text[2], input_text[1], input_text[0])
            if input_text[2] == '':
                add_or_update_first_degree_connection(input_text[1], input_text[0])

        print(input_text)
        print(suggestions)
        print()

if __name__ == "__main__":
    interactive_prompt()

#            add_or_update_word(input_text[0])
#            add_or_update_first_degree_connection(input_text[1], input_text[0])
#            add_or_update_third_degree_connection(input_text[2], input_text[1], input_text[0])


