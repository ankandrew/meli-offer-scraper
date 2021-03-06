import urllib.parse
from typing import Tuple, List

import pandas as pd
import requests
from bs4 import BeautifulSoup
from timeit import default_timer as timer


# TODO:
#   * Check browser vs script item order
#   * reset counter when skip_sponsored
#   * Multiprocessing for requests each link

class Scraper:
    HEADER = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0'
    }
    MELI_URL = 'https://listado.mercadolibre.com.ar/'
    PAGE_ITEMS_CLASS = 'ui-search-layout ui-search-layout--stack'
    URL_CLASS = 'ui-search-item__group__element ui-search-link'
    TRACKING_DEL = '-_JM'  # tracking delimiter
    NEXT_PAGE_CLASS = 'andes-pagination__link ui-search-link'
    SPONSOR_PATTERN = 'https://click1'

    def __init__(self, keyword_search: str,
                 max_queries: int,
                 remove_tracking_info: bool = False,
                 skip_sponsored: bool = False):
        # Ej: keyword_search = 'destornillador bosch'
        # search_url = https://listado.mercadolibre.com.ar/destornillador-bosch
        self.search_url = self.MELI_URL + keyword_search.strip().replace(' ', '-')
        self.max_queries = max_queries
        self.remove_tracking_info = remove_tracking_info
        self.skip_sponsored = skip_sponsored
        self.i = 0
        # Info to export
        self.info = {key: None for key in ['link', 'price', 'vendor']}

    def search(self, verbose: bool = True) -> None:
        # 1. Grab all offers/publications links
        start = timer()
        self._scrap_links()
        links_end = timer()
        # 2. Request each link and grab information
        extract_start = timer()
        self.extract_info()
        end = timer()
        total_time = end - start
        if verbose:
            print(f'*------------TIEMPO----------------*')
            print(f'Buscar links {links_end - start} ({(links_end - start) * 100 / total_time:.0f} %)')
            print(f'Entrar en c/publicacion {end - extract_start} ({(end - extract_start) * 100 / total_time:.0f} %)')
            print(f'Total {total_time}s')
            print(f'*----------------------------------*')

    def extract_info(self) -> None:
        # TODO: Multiprocessing (Faster)
        prices = []
        vendors = []
        for link in self.info['link']:
            soup = self.request_and_parse(link)
            price = soup.find('span', {'class': 'price-tag-fraction'}).text
            vendor = soup.find('a', {'class': 'ui-pdp-media__action ui-box-component__action'}).get('href')
            vendor = urllib.parse.unquote(vendor.split('/')[-1].replace('+', ' '))
            prices.append(price)
            vendors.append(vendor)
        self.info['price'] = prices
        self.info['vendor'] = vendors

    def _scrap_links(self) -> None:
        """
        Scrap offer links with a maximum of self.max_queries offers
        """
        # Download html and parse it
        soup = self.request_and_parse(self.search_url)
        # Find items container
        items_container = soup.find('ol', {'class': self.PAGE_ITEMS_CLASS})
        # Save links to offers
        links, keep_searching = self.iterate_children(items_container)
        next_page_link = self.next_page_available(soup)
        while keep_searching and next_page_link:
            # Send request to next link
            soup = self.request_and_parse(next_page_link)
            # Keep parsing links
            new_links, keep_searching = self.iterate_children(items_container)
            links.extend(new_links)
            next_page_link = self.next_page_available(soup)
        self.info['link'] = links

    def request_and_parse(self, url: str):
        # 1. Send request
        request = requests.get(url, headers=self.HEADER)
        # 2. Check if no item found
        if request.status_code == 404:
            raise ValueError('No se encontro el item!')
        # 3. Parse html
        return BeautifulSoup(request.text, 'lxml')

    def next_page_available(self, soup):
        """
        Check if there is a next page, and returns a link to it if found (otherwise None)
        """
        return soup.find('a', {'class': self.NEXT_PAGE_CLASS}).get('href')

    def iterate_children(self, items_container) -> Tuple[List, bool]:
        """
        Returns true to keep iterating, otherwise false
        Keeps iterating offers as long as counter < self.max_queries
        """
        results = []
        for self.i, list_item in enumerate(items_container.children, start=self.i):
            if self.i >= self.max_queries:
                return results, False
            link = list_item.find('a', {'class': self.URL_CLASS})['href']
            if self.skip_sponsored and self.SPONSOR_PATTERN in link:
                continue
            results.append(self.rm_tracking_info(link))
        return results, True

    def rm_tracking_info(self, link: str) -> str:
        return link[0:link.index(self.TRACKING_DEL) + len(self.TRACKING_DEL)] if self.remove_tracking_info else link

    def export(self):
        pd.DataFrame.from_dict(self.info).to_csv('resultados.csv', index=False)


if __name__ == '__main__':
    scraper = Scraper('boxer', 10, skip_sponsored=False, remove_tracking_info=True)
    scraper.search()
    scraper.export()
