from app.scrapers.interfaces.tvs import TVSScraper
from app.scrapers.BaseScraper import BaseScraper


class tvs(BaseScraper):
    def __init__(self):
        super().__init__(TVSScraper)
