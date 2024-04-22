"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import pathlib
from typing import Pattern, Union
import requests
import re
import json
import random
import time
import datetime

from bs4 import BeautifulSoup
from core_utils.article.io import to_raw, to_meta
from core_utils.article.article import Article
from core_utils import constants
from core_utils.config_dto import ConfigDTO

class IncorrectSeedURLError(Exception):
    pass
class NumberOfArticlesOutOfRangeError(Exception):
    pass

class IncorrectNumberOfArticlesError(Exception):
    pass

class IncorrectHeadersError(Exception):
    pass

class IncorrectEncodingError(Exception):
    pass

class IncorrectTimeoutError(Exception):
    pass

class IncorrectVerifyError(Exception):
    pass


class Config:
    """
    Class for unpacking and validating configurations.
    """

    def __init__(self, path_to_config: pathlib.Path) -> None:
        """
        Initialize an instance of the Config class.

        Args:
            path_to_config (pathlib.Path): Path to configuration.
        """
        self.path_to_config = path_to_config
        self._validate_config_content()
        self.config_dto = self._extract_config_content()

        self._seed_urls = self.config_dto.seed_urls
        self._num_articles = self.config_dto.total_articles
        self._headers = self.config_dto.headers
        self._encoding = self.config_dto.encoding
        self._timeout = self.config_dto.timeout
        self._should_verify_certificate = self.config_dto.should_verify_certificate
        self._headless_mode = self.config_dto.headless_mode

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return ConfigDTO(**config)
            #seed_urls=config['seed_urls'],
            #total_articles_to_find_and_parse=config['total_articles_to_find_and_parse'],
            #headers=config['headers'],
            #encoding=config['encoding'],
            #timeout=config['timeout'],
            #should_verify_certificate=config['should_verify_certificate'],
            #headless_mode=config['headless_mode'])

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if not isinstance(config['seed_urls'], list):
            raise IncorrectSeedURLError

        for seed_url in config['seed_urls']:
            if not re.match('https?://(www.)?', seed_url):
                raise IncorrectSeedURLError

        if not isinstance(config['total_articles_to_find_and_parse'], int) or config['total_articles_to_find_and_parse'] <= 0:
            raise IncorrectNumberOfArticlesError

        if not 1 < config['total_articles_to_find_and_parse'] < 150:
            raise NumberOfArticlesOutOfRangeError

        if not isinstance(config['headers'], dict):
            raise IncorrectHeadersError

        if not isinstance(config['encoding'], str):
            raise IncorrectEncodingError

        if not isinstance(config['timeout'], int) or not 0 < config['timeout'] < 60:
            raise IncorrectTimeoutError

        if not isinstance(config['should_verify_certificate'], bool) or not isinstance(config['headless_mode'], bool):
            raise IncorrectVerifyError

    def get_seed_urls(self) -> list[str]:
        """
        Retrieve seed urls.

        Returns:
            list[str]: Seed urls
        """
        return self._seed_urls

    def get_num_articles(self) -> int:
        """
        Retrieve total number of articles to scrape.

        Returns:
            int: Total number of articles to scrape
        """
        return self._num_articles

    def get_headers(self) -> dict[str, str]:
        """
        Retrieve headers to use during requesting.

        Returns:
            dict[str, str]: Headers
        """
        return self._headers

    def get_encoding(self) -> str:
        """
        Retrieve encoding to use during parsing.

        Returns:
            str: Encoding
        """
        return self._encoding

    def get_timeout(self) -> int:
        """
        Retrieve number of seconds to wait for response.

        Returns:
            int: Number of seconds to wait for response
        """
        return self._timeout

    def get_verify_certificate(self) -> bool:
        """
        Retrieve whether to verify certificate.

        Returns:
            bool: Whether to verify certificate or not
        """
        return self._should_verify_certificate

    def get_headless_mode(self) -> bool:
        """
        Retrieve whether to use headless mode.

        Returns:
            bool: Whether to use headless mode or not
        """
        return self._headless_mode


def make_request(url: str, config: Config) -> requests.models.Response:
    """
    Deliver a response from a request with given configuration.

    Args:
        url (str): Site url
        config (Config): Configuration

    Returns:
        requests.models.Response: A response from a request
    """
    period = random.randrange(10)
    time.sleep(period)

    response = requests.get(url=url, timeout=config.get_timeout(),
                            headers=config.get_headers(),
                            verify=config.get_verify_certificate())

    return response


class Crawler:
    """
    Crawler implementation.
    """

    url_pattern: Union[Pattern, str]

    def __init__(self, config: Config) -> None:
        """
        Initialize an instance of the Crawler class.

        Args:
            config (Config): Configuration
        """
        self.urls = []
        self.config = config
        self.url_pattern = 'https://elementy.ru/novosti_nauki'

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        #url = ''
        #links = article_bs.find_all('a', class_="nohover")
        #for link in links:
        #    url = link.get('href')
        #url = self.url_pattern + url
        #return url

        url = ''
        links = article_bs.find_all('a', class_="nohover")
        for link in links:
            url = link.get('href')
            if url not in self.urls:
                break
        url = self.url_pattern + url[len("/novosti_nauki")::]
        return url

    def find_articles(self) -> None:
        """
        Find articles.
        """
        seed_urls = self.get_search_urls()
        for seed_url in seed_urls:
            response = make_request(seed_url, self.config)

            if not response.ok:
                continue

            #article_bs = BeautifulSoup(response.text, "html.parser")
            #urls = [self._extract_url(article_bs) for i in range(10)]
            #self.urls.extend(urls)

            article_bs = BeautifulSoup(response.text, "html.parser")
            article_url = self._extract_url(article_bs)
            while article_url:
                if len(self.urls) == self.config.get_num_articles():
                    break
                self.urls.append(article_url)
                article_url = self._extract_url(article_bs)

            if len(self.urls) == self.config.get_num_articles():
                break

    def get_search_urls(self) -> list:
        """
        Get seed_urls param.

        Returns:
            list: seed_urls param
        """
        return self.config.get_seed_urls()

# 10
# 4, 6, 8, 10


class HTMLParser:
    """
    HTMLParser implementation.
    """

    def __init__(self, full_url: str, article_id: int, config: Config) -> None:
        """
        Initialize an instance of the HTMLParser class.

        Args:
            full_url (str): Site url
            article_id (int): Article id
            config (Config): Configuration
        """
        self.full_url = full_url
        self.article_id = article_id
        self.config = config
        self.article = Article(self.full_url, self.article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """

        #article = ''
        #article_texts = article_soup.find(class_="memo")
        #texts = article_texts.find_all('p')
        #for text in texts:
        #    article += text.text + '\n'
        #self.article.text = article

        #print(self.article.text)

        for clas in article_soup.find_all(class_='small'):
            clas.decompose()

        text = article_soup.find(class_="memo")
        full_text = ''
        all_p_tags = text.find_all("p", recursive=False)[:-1]

        for p in all_p_tags:
            full_text += p.text + '\n'
        self.article.text = full_text

        #raw_text = ''
        #article_texts = article_soup.find(class_="memo")
        #text_blocks = article_texts.find_all('p')
        #for text_block in text_blocks:
        #    if text_block.string:
        #        raw_text += f'\n{text_block.string}'
#
        #self.article.text = raw_text
        #print(raw_text)

        #all_div = article_soup.find(class_="memo")
        #full_text = ''
        #all_p_tags = all_div.find_all("p", recursive=False)[:-1]
#
        #for p in all_p_tags:
        #    full_text += p.text + '\n'
        #self.article.text = full_text
        #print(self.article.text)

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        self.article.title = str(article_soup.find(class_='title').string)
        print(self.article.title)

        author = article_soup.find_all('p')[-1]
        author = author.get_text()
        if author:
            self.article.author = [author]
        else:
            self.article.author = ["NOT FOUND"]
        print(self.article.author)

        #author = str(article_soup.find('i', class_="small"))
        #if author:
        #    self.article.author = [author]
        #else:
        #    self.article.author = ["NOT FOUND"]
#
        #print(self.article.author)

        #author = article_soup.find_all('i', class_='small')[-1]
        #print(author)

        date = article_soup.find('span', class_='date')
        self.article.date = date
        print(self.article.date)

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """

    def parse(self) -> Union[Article, bool, list]:
        """
        Parse each article.

        Returns:
            Union[Article, bool, list]: Article instance
        """
        response = make_request(self.full_url, self.config)
        if response.ok:
            article_bs = BeautifulSoup(response.text, 'html.parser')
            self._fill_article_with_text(article_bs)
            self._fill_article_with_meta_information(article_bs)

        return self.article


def prepare_environment(base_path: Union[pathlib.Path, str]) -> None:
    """
    Create ASSETS_PATH folder if no created and remove existing folder.

    Args:
        base_path (Union[pathlib.Path, str]): Path where articles stores
    """
    base_path.mkdir(parents=True, exist_ok=True)

    for file in base_path.iterdir():
        file.unlink(missing_ok=True)

def main() -> None:
    """
    Entrypoint for scrapper module.
    """
    configuration = Config(path_to_config=constants.CRAWLER_CONFIG_PATH)
    crawler = Crawler(configuration)
    base_path = constants.ASSETS_PATH
    prepare_environment(base_path)
    crawler.find_articles()

    for i, full_url in enumerate(crawler.get_search_urls()):
        parser = HTMLParser(full_url=full_url, article_id=i, config=configuration)
        article = parser.parse()
        to_raw(article)
        to_meta(article)


if __name__ == "__main__":
    main()
