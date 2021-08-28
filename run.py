import argparse
from offer_scraper.scraper import Scraper


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('keyword', help='Nombre del item/producto a buscar')
    parser.add_argument('max_queries', type=int, help='Cantidad maxima a buscar')
    parser.add_argument('--skip_sponsor', action='store_true', help='Saltear los productos sponsoreados')
    parser.add_argument('--remove_tracking', action='store_true', help='Remover el tracking de la url a guardar')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    scraper = Scraper(args.keyword,
                      args.max_queries,
                      skip_sponsored=args.skip_sponsor,
                      remove_tracking_info=args.remove_tracking)
    scraper.search()
    scraper.export()
