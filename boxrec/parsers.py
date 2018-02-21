import lxml.html
from .models import Fight, Boxer

class FailedToParse(Exception):
    pass

class BaseParser(object):
    def __init__(self):
        pass

    def make_dom_tree(self, response):
        encoding = response.encoding
        binary_contents = response.content

        lxml_parser = lxml.html.HTMLParser(encoding=response.encoding)
        tree = lxml.html.document_fromstring(
            response.content,
            parser=lxml_parser
        )

        return tree


class FightParser(BaseParser):
    BASE_DOM_PATH = \
        '//div[@class="singleColumn"]//table[@class="responseLessDataTable"]/tr'

    def get_event_and_fight_id(self, url):
        splitted = url.rsplit('/')

        event_id = splitted[-2]
        fight_id = splitted[-1]
        return event_id, fight_id

    def get_boxer_ids(self, tree):
        boxer_links = tree.xpath(
            FightParser.BASE_DOM_PATH + '[1]//a[@class="personLink"]/@href'
        )

        try:
            left = boxer_links[0].rsplit('/')[-1]
            right = boxer_links[1].rsplit('/')[-1]
        except IndexError:
            raise FailedToParse("[-] Could not get boxers for fight")

        return left, right

    def clean_rating(self,raw):
        return int(raw.rsplit('\n')[0].replace(',',''))

    def get_rating_before_fight(self, tree):
        rating_row = tree.xpath(
            FightParser.BASE_DOM_PATH + '[./td/b/text() = "before fight"]/td/text()'
        )
        try:
            rating_left,rating_right = rating_row
        except ValueError:
            raise FailedToParse("[-] Missing rating for fight")


        return self.clean_rating(rating_left), self.clean_rating(rating_right)


    def get_fight_outcome(self,tree):
        pass

    def parse(self, response):
        tree = self.make_dom_tree(response)


        event_id, fight_id = self.get_event_and_fight_id(response.url)
        boxer_left_id, boxer_right_id = self.get_boxer_ids(tree)
        rating_left,rating_right = self.get_rating_before_fight(tree)
        ##result = self.get_fight_outcome(tree)

        return Fight(
            event_id = event_id,
            fight_id = fight_id,
            boxer_left_id = boxer_left_id,
            boxer_right_id = boxer_right_id,
            winner = 'left'
        )


class FightListParser(BaseParser):
    BASE_DOM_PATH = \
        '//div[@class="content"]//table[@class="calendarTable"]'

    def get_event_and_fight_ids(self, tree):
        links = tree.xpath(
            FightListParser.BASE_DOM_PATH \
                + '//td[@class="actionCell"]/div[@class="mobileActions"]/a[1]/@href'
        )

        events = map(lambda x: x.rsplit('/')[-2], links)
        fights = map(lambda x: x.rsplit('/')[-1], links)

        return events, fights


    def parse(self, response):
        tree = self.make_dom_tree(response)

        event_ids, fight_ids = \
            self.get_event_and_fight_ids(tree)

        return zip(event_ids, fight_ids)


class BoxerParser(BaseParser):
    BASE_DOM_PATH = \
        '//div[@class="singleColumn"]//table[@class="profileTable"][1]'

    def get_boxer_id(self, url):
        return url.rsplit('/')[-1]

    def get_boxer_name(self, tree):
        return tree.xpath(
            BoxerParser.BASE_DOM_PATH + '//h1/text()'
        )[0]

    def parse(self, response):
        tree = self.make_dom_tree(response)

        boxer_id = self.get_boxer_id(response.url)
        boxer_name = self.get_boxer_name(tree)

        return Boxer(
            id = boxer_id,
            name = boxer_name
        )
