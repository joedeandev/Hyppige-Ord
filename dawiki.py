import re
import xml.etree.ElementTree as ElementTree
from argparse import ArgumentParser
from collections import defaultdict
from html import unescape
from os import listdir, remove
from os.path import exists, getsize, splitext
from sqlite3 import IntegrityError, connect
from time import time

try:
    from tqdm import tqdm
except (ImportError, ModuleNotFoundError):
    tqdm = None


def parse_words(xml_path: str, show_progress=False) -> dict[str, int]:
    words = defaultdict(int)

    allowed_chars = "abcdefghijklmnopqrstuvwxyzæøåABCDEFGHIJKLMNOPQRSTUVWXYZÆØÅéÉ-"
    broken_words = re.compile(r"\S*[^\s" + allowed_chars + r"]\S*")
    disallowed_chars = re.compile(r"[^" + allowed_chars + r"]")
    template = re.compile(r"\{.*?}")
    special_link = re.compile(r"\[\[.*?:.*?]]")
    url_text = re.compile(r"(www|https?)\S+", flags=re.IGNORECASE)

    xml_file_size = getsize(xml_path)
    progress_bar = tqdm(total=xml_file_size) if tqdm and show_progress else None
    previous_progress = -1
    with open(xml_path, "r", encoding="utf-8") as xml_file:
        for event, element in ElementTree.iterparse(xml_file, events=("end",)):
            # splits off the xml namespace from the tag
            if element.tag.split("}")[-1] not in ["title", "text"]:
                continue
            # some elements are apparently without text: we ignore these
            if element.text is None:
                continue

            # remove html escapes
            text = unescape(element.text)
            # filter out any templates (sacrifices quantity for quality)
            text = template.sub(" ", text)
            # filter special links, especially files
            text = special_link.sub(" ", text)
            # filter out urls
            text = url_text.sub(" ", text)
            # limit to words that use only allowed characters
            text = broken_words.sub(" ", text)
            # filter out any other disallowed characters
            text = disallowed_chars.sub(" ", text)

            for word in re.split(r"\s", text):
                # ignore empty strings and strings that start or end with '-'
                if len(word) < 1 or "-" in [word[0], word[-1]]:
                    continue
                words[word] += 1

            element.clear()

            file_progress = xml_file.tell()
            if progress_bar and show_progress:
                progress_bar.update(file_progress - progress_bar.n)
            elif show_progress:
                progress_percent = int(100 * (file_progress / xml_file_size))
                if progress_percent != previous_progress:
                    previous_progress = progress_percent
                    print(f"{progress_percent}%, " f"{file_progress}/{xml_file_size}")

    if progress_bar is not None:
        progress_bar.close()

    return words


def insert_words(db_path: str, words: dict[str, int], show_progress=False) -> None:
    progress_bar = tqdm(total=len(words) * 2) if tqdm and show_progress else None

    connection = connect(db_path)
    cursor = connection.cursor()

    cursor.execute(
        'CREATE TABLE "words" ('
        '   "word" TEXT NOT NULL UNIQUE, '
        '   "count" INTEGER NOT NULL, PRIMARY KEY("word")'
        ");"
    )
    # executemany is faster, but takes massive amounts of memory
    for word, count in words.items():
        cursor.execute("INSERT INTO words VALUES (?, ?)", (word, count))
        if progress_bar and show_progress:
            progress_bar.update(1)

    # a little hack - whenever a collision is encountered, add the values together
    cursor.execute(
        'CREATE TABLE "words_nocase" ('
        '   "word" TEXT NOT NULL UNIQUE, '
        '   "count" INTEGER NOT NULL, PRIMARY KEY("word")'
        ");"
    )
    for word, count in words.items():
        word = word.lower()
        try:
            cursor.execute("INSERT INTO words_nocase VALUES (?, ?)", (word, count))
        except IntegrityError as e:
            if not str(e).startswith("UNIQUE constraint failed"):
                raise e
            cursor.execute("SELECT count FROM words_nocase WHERE word = ?", (word,))
            count += cursor.fetchone()[0]
            cursor.execute(
                "UPDATE words_nocase SET count = ? WHERE word = ?", (count, word)
            )
        if progress_bar and show_progress:
            progress_bar.update(1)
    connection.commit()
    connection.close()

    if progress_bar is not None:
        progress_bar.close()


def write_csv(csv_path: str, db_path: str) -> None:
    connection = connect(db_path)
    cursor = connection.cursor()

    for nocase in [False, True]:
        table = "words_nocase" if nocase else "words"
        output_path = (
            splitext(csv_path)[0] + "-nocase" + splitext(csv_path)[1]
            if nocase
            else csv_path
        )
        cursor.execute(f"SELECT SUM(count) FROM {table}")
        total_words = cursor.fetchone()[0]
        cursor.execute(f"SELECT * FROM {table} ORDER BY count DESC")
        with open(output_path, "w", encoding="utf8") as csv_file:
            csv_file.write(",".join(["Word", "Count", "Frequency"]) + "\n")
            for word, count in cursor.fetchall():
                csv_file.write(
                    ",".join([str(_) for _ in [word, count, count / total_words]])
                    + "\n"
                )

    connection.close()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "xml_path",
        nargs="?",
        default=[f for f in listdir() if f.endswith(".xml")][0],
        help="path (relative/absolute) to dawiki/wikimedia dump",
    )
    parser.add_argument(
        "db_path",
        nargs="?",
        default="dawiki.db",
        help="path (relative/absolute) to sqlite database",
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="da-words.csv",
        help="path (relative/absolute) to export file",
    )
    parser.add_argument(
        "-f",
        "--force-recreate",
        dest="force_recreate",
        nargs="?",
        const=True,
        default=False,
        help="Including this flag force-rebuilds the word database, and deletes the previous one.",
    )
    arguments = parser.parse_args()
    start_time = time()
    if not exists(arguments.db_path) or arguments.force_recreate:
        if exists(arguments.db_path):
            print(f"Removing {arguments.db_path}")
            remove(arguments.db_path)
        print(f"Extracting words from {arguments.xml_path}")
        found_words = parse_words(arguments.xml_path, True)
        print(f"Inserting {len(found_words)} words into {arguments.db_path}")
        insert_words(arguments.db_path, found_words)
    else:
        found_words = {}
    print(f"Writing to {arguments.csv_path}")
    write_csv(arguments.csv_path, arguments.db_path)
    print(f"Processed {len(found_words)} words in {int(time() - start_time)} seconds")
