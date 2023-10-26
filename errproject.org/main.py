import argparse
import json
from datetime import datetime
import scraper

parser = argparse.ArgumentParser(prog='errproject.org scraper')
parser.add_argument('--offset', type=int, default=1, help='Offset to start scraping from')
parser.add_argument('--limit', type=int, default=100000, help='Number of cards to scrape')
parser.add_argument('--quiet', action='store_true', help='Suppress output')
parser.add_argument('--output', type=str, help='Output file name or path')
args = parser.parse_args()

default_filename = datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + "_errproject.org.json"
filename = args.output if args.output else default_filename

with open(filename, "w") as file:
    cards = list()
    counter = 1

    for card in scraper.scrape_cards(limit=args.limit, offset=args.offset):
        if not args.quiet:
            print("Scraped card no " + str(counter) + " - id " + str(card["id"]))

        cards.append(card)
        counter += 1

    json.dump(cards, file, indent=2)
