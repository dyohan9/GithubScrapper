import scrapy
from scrapy import FormRequest

from github.items import GithubItem


class GithubSpider(scrapy.Spider):
    name = "github_spider"
    username_github = ""
    password_github = ""

    def save_file(self, response, filename, filemode="wb"):
        with open(filename, filemode) as handle:
            handle.write(response.body)
        return filename

    def get_absolute_url(self, path):
        return f"https://github.com{path}"

    def get_stargazers(self, repository):
        return f"{self.get_absolute_url(repository)}/stargazers"

    def start_requests(self):
        yield scrapy.Request(
            "https://github.com/login", meta={}, callback=self.parse_login
        )

    def parse_login(self, response):
        yield FormRequest.from_response(
            response,
            url="https://github.com/session",
            method="POST",
            formdata={"login": self.username_github, "password": self.password_github},
            callback=self.start_crawler,
        )

    def start_crawler(self, response):
        for search in ["rasa", "spacy", "rocket", "machine+learning"]:
            yield scrapy.Request(
                f"https://github.com/search?q={search}",
                meta=response.meta,
                callback=self.parse_repositories_page,
            )

    def parse_repositories_page(self, response):
        page = response.xpath('//div/main/div/div/div/div/div/a[@class="next_page"]')
        if page:
            page = page.xpath("./@href").extract_first()
            yield scrapy.Request(
                self.get_absolute_url(page), meta=response.meta, callback=self.parse
            )
            yield scrapy.Request(
                self.get_absolute_url(page),
                meta=response.meta,
                callback=self.parse_repositories_page,
            )

    def parse(self, response):
        for li in response.xpath("//div[4]/main/div/div[3]/div/ul/li"):
            repository = li.xpath("./div[2]/div[1]/a/@href").extract_first()
            yield scrapy.Request(
                self.get_stargazers(repository),
                callback=self.parse_stargazers,
                meta={"repository": repository},
            )

    def parse_stargazers(self, response):
        for li in response.xpath("//div/div/main/div/div/div/ol/li"):
            user_profile = li.xpath("./div/h3/span/a/@href").extract_first()
            yield scrapy.Request(
                self.get_absolute_url(user_profile),
                callback=self.parse_profile,
                meta=response.meta,
            )

        next_page = response.xpath(
            "//div/div/main/div/div/div/div/div/*[contains"
            '(@class, "btn btn-outline BtnGroup-item")][2]/@href'
        ).extract_first()

        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(
                next_page, callback=self.parse_stargazers, meta=response.meta
            )

    def parse_profile(self, response):
        email = response.xpath(
            '//div/main/div/div/div/div/ul/li/a[@class="u-email "]/@href'
        )
        if len(email) > 0:
            item = GithubItem()
            item["email"] = email.extract_first().replace("mailto:", "")
            yield item
