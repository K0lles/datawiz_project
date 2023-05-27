from django.test import TestCase


class ShopAppTest(TestCase):

    def test_shop_group(self):
        response = self.client.get(
            path='/shops/shop-group/'
        )
        self.assertEquals(response.status_code, 200)

    def test_non_existing_id_shop_group(self):
        response = self.client.get(
            path='/shops/shop-group/87987879889/?name=MegaTest&page_size=200'
        )
        self.assertEquals(bool(response.json().get('detail', None)), True)

    def test_non_existing_shop_group_page(self):
        response = self.client.get(
            path='/shops/shop-group/?page_size=200&page=78364576347856'
        )
        self.assertEquals(response.status_code, 404)

    def test_shop(self):
        response = self.client.get(
            path='/shops/shop/'
        )
        self.assertEquals(response.status_code, 200)

    def test_non_existing_id_shop(self):
        response = self.client.get(
            path='/shops/shop/87987879889/?name=MegaTest&page_size=200'
        )
        self.assertEquals(bool(response.json().get('detail', None)), True)

    def test_non_existing_shop_page(self):
        response = self.client.get(
            path='/shops/shop/?page_size=200&page=78364576347856'
        )
        self.assertEquals(response.status_code, 404)
