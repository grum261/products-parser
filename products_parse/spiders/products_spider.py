import scrapy

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from shutil import which

# Пока работает только для Челябинска
class ProductsSpider(scrapy.Spider):
    name = 'products'
    base_url = 'https://krasnoeibeloe.ru'
    start_urls = ['https://krasnoeibeloe.ru/catalog/', ]

    def parse(self, response):
        categories = response.xpath('//div[@class="catalog_top_sections__item__name"]/a/@href')
        for category in categories:
            if category:
                yield response.follow(category, callback=self.parse_products)

    def parse_products(self, response):
        products = response.xpath('//div[@class="catalog_product_item_cont"]')

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')

        driver = webdriver.Chrome(which('chromedriver'), chrome_options=chrome_options)
        driver.get(response.url)

        prices = []
        for price in driver.find_elements_by_class_name('catalog_product_item_cont'):
            try:
                prices.append(price.find_element_by_class_name('i_price').text)
            except NoSuchElementException:
                prices.append(None)

        for idx, product in enumerate(products):
            characteristics = product.xpath('./div[@class="product_item_name"]/p/text()').get().split(', ') # 0.75 л., Франция, Лангедок Руссийон, 11.5%

            # Если длина характеристик 3, то у продукта нет региона проихсождения и мы заменяем его на None
            if len(characteristics) == 3:
                tmp = characteristics.pop()
                characteristics.extend([None, tmp])
            # Если длин 2, то продукт безалкогольный и без региона, добавляем в конец списка [None, None]
            elif len(characteristics) == 2:
                characteristics.extend([None, None])

            yield {
                'name': product.xpath('./div[@class="product_item_name"]/a/text()').get(),
                'price': prices[idx],
                'volume': characteristics[0],
                'origin': {
                    'country': characteristics[1],
                    'region': characteristics[2]
                },
                'alcohol': characteristics[3],
                'url': self.base_url + product.xpath('./div[@class="product_item_name"]/a/@href').get()
            }

        next_page = response.xpath('//li[@class="pag_arrow_right"]/a/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_products)

        driver.quit()