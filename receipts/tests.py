from django.test import TestCase


class ReceiptAppTest(TestCase):

    def test_terminal(self):
        response = self.client.get(
            path='/receipts/terminal/'
        )
        self.assertEquals(response.status_code, 200)

    def test_non_existing_id_terminal(self):
        response = self.client.get(
            path='/receipts/terminal/87987879889/?name=MegaTest&page_size=200'
        )
        self.assertEquals(bool(response.json().get('detail', None)), True)

    def test_non_existing_terminal_page(self):
        response = self.client.get(
            path='/receipts/terminal/?page_size=200&page=78364576347856'
        )
        self.assertEquals(response.status_code, 404)

    def test_supplier(self):
        response = self.client.get(
            path='/receipts/supplier/'
        )
        self.assertEquals(response.status_code, 200)

    def test_non_existing_id_supplier(self):
        response = self.client.get(
            path='/receipts/supplier/87987879889/?name=MegaTest&page_size=200'
        )
        self.assertEquals(bool(response.json().get('detail', None)), True)

    def test_non_existing_supplier_page(self):
        response = self.client.get(
            path='/receipts/supplier/?page_size=200&page=78364576347856'
        )
        self.assertEquals(response.status_code, 404)
