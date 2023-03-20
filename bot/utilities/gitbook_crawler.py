import os
import requests
from bs4 import BeautifulSoup


def download_page_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    content = soup.get_text()
    return content


def download_site_content(url, download_dir):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    for link in soup.find_all("a"):
        href = link.get("href")
        if href.startswith("http"):
            continue
        page_url = url + href

        print(f"Downloading {page_url}...")
        content = download_page_content(page_url)
        filename = href.replace("/", "_") + ".txt"
        filepath = os.path.join(download_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)


def main():
    url = "https://docs.aave.com/hub/"
    download_dir = "aave"
    os.makedirs(download_dir, exist_ok=True)
    content = download_page_content(url)
    with open(download_dir + "test.txt", "w") as f:
        f.write(content)


if __name__ == "__main__":
    main()
