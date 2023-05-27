from django.test import TestCase


class ProductAppTest(TestCase):

    def test_category(self):
        response = self.client.get(
            path='/products/category/'
        )
        self.assertEquals(response.status_code, 200)

    def test_non_existing_id_category(self):
        response = self.client.get(
            path='/products/category/87987879889/?name=MegaTest&page_size=200'
        )
        self.assertEquals(bool(response.json().get('detail', None)), True)

    def test_non_existing_category_page(self):
        response = self.client.get(
            path='/products/category/?page_size=200&page=78364576347856'
        )
        self.assertEquals(response.status_code, 404)

    def test_producers(self):
        response = self.client.get(
            path='/products/producer/'
        )
        self.assertEquals(response.status_code, 200)

    def test_products(self):
        response = self.client.get(
            path='/products/product/?category=MegaTest&ordering=-name&page_size=200'
        )
        self.assertEquals(response.status_code, 200)

    def test_non_existing_id_product(self):
        response = self.client.get(
            path='/products/product/87987879889/?category=MegaTest&ordering=-name&page_size=200'
        )
        self.assertEquals(response.status_code, 400)

    def test_non_existing_category_products(self):
        response = self.client.get(
            path='/products/product/?category=bjfngbjknfg&ordering=-name&page_size=200'
        )
        self.assertEquals(response.status_code, 200)
