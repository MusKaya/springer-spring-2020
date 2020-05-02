# -*- coding: utf-8 -*-
import os
import time
import requests
import argparse
import traceback
import subprocess
import pandas as pd
from tqdm import tqdm

DOWNLOAD_DIR = 'downloads'
BOOK_LIST_URL = 'https://resource-cms.springernature.com/springer-cms/rest/v1/content/17858272/data/v4'
BOOK_LIST_FILE = 'book_list.xlsx'
PDF_LIST_FILE = 'pdf_list.xlsx'
EPUB_LIST_FILE = 'epub_list.xlsx'
DOWNLOAD_LIST_FAILURES = 'download_list_failures.xlsx'
PDF_DOWNLOAD_FAILURES = 'pdf_download_failures.xlsx'
EPUB_DOWNLOAD_FAILURES = 'epub_download_failures.xlsx'


def build_clean_filename(file_url, file_extension, title, author):
    final = file_url.split('/')[-1]
    filename = title.replace(',','-').replace('.','').replace('/',' ').replace(':',' ') + ' - ' + author.replace(',','-').replace('.','').replace('/',' ').replace(':',' ') + ' - ' + final
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    filename = (filename[:145] + file_extension) if len(filename) > 145 else filename

    return filename


def build_pdf_url_and_filename(book_url, title, author):
    pdf_url = book_url.replace('/book/', '/content/pdf/')
    pdf_url = pdf_url.replace('%2F', '/')
    pdf_url = pdf_url + '.pdf'

    pdf_filename = build_clean_filename(pdf_url, '.pdf', title, author)

    return pdf_url, pdf_filename


def build_epub_url_and_filename(book_url, title, author):
    epub_url = book_url.replace('/book/', '/download/epub/')
    epub_url = epub_url.replace('%2F', '/')
    epub_url = epub_url + '.epub'

    epub_filename = build_clean_filename(epub_url, '.epub', title, author)

    return epub_url, epub_filename


def get_book_list(steps):
    print("\nSTEP 1/{}: Retrieving book list from Springer.".format(steps))
    download_dir = os.path.join(os.getcwd(), DOWNLOAD_DIR)
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)

    book_list_file = os.path.join(download_dir, BOOK_LIST_FILE)
    if not os.path.exists(book_list_file):
        books = pd.read_excel(BOOK_LIST_URL)
        books.to_excel(book_list_file)
        print("LOG: Retrieved book list from Springer and saved as {}".
              format(book_list_file))
    else:
        books = pd.read_excel(book_list_file, index_col=0, header=0)
        print("LOG: Already found the book list downloaded as {}".
              format(book_list_file))

    return books


def build_download_list(books, steps):
    print("\nSTEP 2/{}: Building download lists.".format(steps))
    download_dir = os.path.join(os.getcwd(), DOWNLOAD_DIR)
    pdf_list_path = os.path.join(download_dir, PDF_LIST_FILE)
    epub_list_path = os.path.join(download_dir, EPUB_LIST_FILE)
    pdf_list_done, epub_list_done = False, False

    if os.path.exists(pdf_list_path):
        print("LOG: Already found the pdf download list downloaded as {}".
              format(pdf_list_path))
        pdf_list_done = True

    if os.path.exists(epub_list_path):
        print("LOG: Already found the epub download list downloaded as {}".
              format(epub_list_path))
        epub_list_done = True

    if pdf_list_done and epub_list_done:
        return pdf_list_path, epub_list_path

    download_list_failures_path = os.path.join(download_dir, DOWNLOAD_LIST_FAILURES)
    download_list_failures = {'package_name': [], 'url': [], 'traceback': []}

    if not pdf_list_done:
        pdf_list = {'subject': [], 'url': [], 'filename': []}
    if not epub_list_done:
        epub_list = {'subject': [], 'url': [], 'filename': []}

    for url, title, author, pk_name in tqdm(books[['OpenURL', 'Book Title', 'Author', 'English Package Name']].values):
        try:
            with requests.get(url, stream=True) as res:
                book_url = res.url
                if not pdf_list_done:
                    pdf_url, pdf_filename = build_pdf_url_and_filename(book_url, title, author)
                    pdf_list['subject'].append(pk_name)
                    pdf_list['url'].append(pdf_url)
                    pdf_list['filename'].append(pdf_filename)
                if not epub_list_done:
                    epub_url, epub_filename = build_epub_url_and_filename(book_url, title, author)
                    epub_list['subject'].append(pk_name)
                    epub_list['url'].append(epub_url)
                    epub_list['filename'].append(epub_filename)
        except Exception:
            print('ERROR: Could not add items to the download_list for the following:')
            print('subject: {}, url: {}'.format(pk_name, url))
            print(traceback.format_exc())
            download_list_failures['package_name'].append(pk_name)
            download_list_failures['url'].append(url)
            download_list_failures['traceback'].append(traceback.format_exc())

    if not pdf_list_done:
        df = pd.DataFrame(pdf_list, columns=['subject', 'url', 'filename'])
        df.to_excel(pdf_list_path)

    if not epub_list_done:
        df = pd.DataFrame(epub_list, columns=['subject', 'url', 'filename'])
        df.to_excel(epub_list_path)

    if download_list_failures.get('url'):
        df = pd.DataFrame(download_list_failures, columns=['package_name', 'url', 'traceback'])
        df.to_excel(download_list_failures_path)

    return pdf_list_path, epub_list_path


def download_books(download_list_path, steps):
    download_dir = os.path.join(os.getcwd(), DOWNLOAD_DIR)
    if download_list_path.endswith(PDF_LIST_FILE):
        print("\nSTEP 3/{}: Downloading pdf files.".format(steps))
        download_failures_path = os.path.join(download_dir, PDF_DOWNLOAD_FAILURES)
    elif download_list_path.endswith(EPUB_LIST_FILE):
        print("\nSTEP 4/4: Downloading epub files.")
        download_failures_path = os.path.join(download_dir, EPUB_DOWNLOAD_FAILURES)
    else:
        print('ERROR: Could not resolve the download failures filename '
              + 'from the provided download list: {}'.format(download_list_path))
        print('Exiting...')
        return False

    download_failures = {'subject': [], 'url': [], 'filename': [], 'traceback': []}
    download_list = pd.read_excel(download_list_path, index_col=0, header=0)

    for subject, url, filename in tqdm(download_list[['subject', 'url', 'filename']].values):
        try:
            subject_dir = os.path.join(download_dir, subject)
            filepath = os.path.join(subject_dir, filename)

            if not os.path.exists(subject_dir):
                os.mkdir(subject_dir)

            if not os.path.exists(filepath):
                with requests.get(url, stream=True) as response:
                    if response.ok:
                        with open(filepath, 'wb') as out_file:
                            for chunk in response.iter_content(chunk_size=128):
                                out_file.write(chunk)
                    else:
                        print('LOG: Not found: {}. Skipping...'.format(filename))
            else:
                print('LOG: Already present: {}. Directory: {}. Skipping...'.format(filename, subject))
        except requests.exceptions.ConnectionError:
            if os.path.exists(filepath):
                os.remove(filepath)
            print('WARN: Could not download the following items. Will try via wget:')
            print('subject: {}, url: {}, filename: {}'.format(subject, url, filename))
            time.sleep(10)
            sub_res = subprocess.run(["bash", "-c", "wget {} -O '{}'"
                                     .format(url, filepath)])
            if sub_res.returncode != 0:
                raise
        except Exception:
            if os.path.exists(filepath):
                os.remove(filepath)
            print('ERROR: Could not download the following items:')
            print('subject: {}, url: {}, filename: {}'.format(subject, url, filename))
            print(traceback.format_exc())
            download_failures['subject'].append(subject)
            download_failures['url'].append(url)
            download_failures['filename'].append(filename)
            download_failures['traceback'].append(traceback.format_exc())

    if download_failures.get('url'):
        df = pd.DataFrame(download_failures, columns=['subject', 'url', 'filename', 'traceback'])
        df.to_excel(download_failures_path)


def main(filetype, steps):
    books = get_book_list(steps)
    pdf_list_path, epub_list_path = build_download_list(books, steps)
    if filetype == 'pdf' or filetype == 'all':
        download_books(pdf_list_path, steps)
    if filetype == 'epub' or filetype == 'all':
        download_books(epub_list_path, steps)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Utility script to download all books made available by Springer during Spring 2020.")
    parser.add_argument('--type', nargs='?', choices=('pdf', 'epub', 'all'), const='pdf', default='pdf')
    args = parser.parse_args()
    steps = 4 if args.type == 'all' else 3
    main(args.type, steps)
