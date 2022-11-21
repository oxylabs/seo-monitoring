import time
import nltk
import pandas as pd

from pathlib import Path
from nltk.corpus import stopwords
from os import listdir, rename
from os.path import isfile, join

from pandas import ExcelWriter


def _current_milli_time():
    return round(time.time() * 1000)


def check_for_new_input_files(directory_path: str) -> list:
    return [(directory_path, f) for f in listdir(directory_path) if
            isfile(join(directory_path, f)) and not f.startswith(".")]


def move_processed_input_file(source_path: str, file_name: str, destination_path: str):
    rename(join(source_path, file_name),
           join(destination_path, f"{_current_milli_time()}-{file_name}"))


def read_keywords_input_file(file_path: str, file_name: str) -> list:
    file_extension = ''.join(Path(file_name).suffixes)
    keywords_list = []
    df = pd.DataFrame()
    if file_extension == ".csv":
        try:
            df = pd.read_csv(file_path)
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding="utf-16", sep=None, engine="python")
    elif file_extension in [".xls", ".xlsx"]:
        df = pd.read_excel(file_path)
    try:
        df.columns = map(str.lower, df.columns)
        keywords_list = df["keyword"].tolist()
    except Exception as e:
        print(f"No Keywords column found, {str(e)}")
    return _parse_tokenized_keywords([x.lower() for x in set(keywords_list) if keywords_list])


def _parse_tokenized_keywords(keywords_list: list) -> list:
    processed_words = []
    if keywords_list:
        keywords = ' '.join(keywords_list)
        stop_words = set(stopwords.words("english"))
        tokens = nltk.word_tokenize(keywords)
        filtered_tokens = [word for word in tokens if word not in stop_words]
        filtered = filter(lambda x: x if len(x) > 1 else "", filtered_tokens)
        if filtered:
            all_words = nltk.FreqDist(filtered)
            common_processed_words = all_words.most_common(100)
            for word in common_processed_words:
                processed_words.append(word[0])
    return processed_words


def make_output_file(results: list, file_type: str, file_name: str, destination_path: str,
                     use_header: bool = False):
    df = pd.DataFrame(results)
    dst_file_name_type = f"{_current_milli_time()}-{file_name}.{file_type}"
    dst_file_path = join(destination_path, dst_file_name_type)
    match file_type:
        case "csv":
            df.to_csv(dst_file_path, index=False, header=use_header)
        case "xlsx":
            with ExcelWriter(dst_file_path) as writer:
                df.to_excel(writer, index=False, header=use_header)
        case _:
            return False
    return {"file_path": dst_file_path, "file_type": file_type, "file_name": dst_file_name_type}
