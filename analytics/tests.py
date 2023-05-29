from django.test import TestCase


class AnalyticsAppTest(TestCase):

    def test_product_analytics_turnover(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [{'name': 'product'}],
                'metrics': [{'name': 'turnover'}],
                'date_range': ['2022-01-01', '2022-01-20']
            },
            content_type='application/json'
        )
        self.assertIsInstance(response.json().get('results', None), list)

    def test_product_turnover_diff_diff_percent(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [{'name': 'product'}],
                'metrics': [{'name': 'turnover'}, {'name': 'turnover_diff'}, {'name': 'turnover_diff_percent'}],
                'date_range': ['2022-02-01', '2022-02-20'],
                'prev_date_range': ['2022-01-01', '2022-01-20']
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_shop_product_turnover_diff_percent(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [{'name': 'shop'}, {'name': 'product'}],
                'metrics': [{'name': 'turnover'}, {'name': 'turnover_diff'}, {'name': 'turnover_diff_percent'}],
                'date_range': ['2022-02-01', '2022-02-20'],
                'prev_date_range': ['2022-01-01', '2022-01-20']
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_supplier_product_turnover(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [{'name': 'supplier'}, {'name': 'product'}],
                'metrics': [{'name': 'turnover'}, {'name': 'turnover_diff'}, {'name': 'turnover_diff_percent'}],
                'date_range': ['2022-02-01', '2022-02-20'],
                'prev_date_range': ['2022-01-01', '2022-01-20']
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_all_dimensions(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [{'name': 'shop'}, {'name': 'group'}, {'name': 'producer'},
                               {'name': 'supplier'}, {'name': 'product'}],
                'metrics': [{'name': 'turnover'}, {'name': 'sold_product_amount'}, {'name': 'turnover_diff_percent'},
                            {'name': 'income'}],
                'date_range': ['2022-02-01', '2022-02-20'],
                'prev_date_range': ['2022-01-01', '2022-01-20']
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_incorrect_date_range(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [{'name': 'shop'}, {'name': 'group'}, {'name': 'producer'},
                               {'name': 'supplier'}, {'name': 'product'}],
                'metrics': [{'name': 'turnover'}, {'name': 'sold_product_amount'}, {'name': 'turnover_diff_percent'},
                            {'name': 'income'}],
                'date_range': ['2022-02-01', '2022-01-20'],
                'prev_date_range': ['2022-01-20', '2022-01-19']
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_nullable_dimensions(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [],
                'metrics': [{'name': 'turnover'}, {'name': 'sold_product_amount'}, {'name': 'turnover_diff_percent'},
                            {'name': 'income'}],
                'date_range': ['2022-02-01', '2022-01-20'],
                'prev_date_range': ['2022-01-20', '2022-01-19']
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_nullable_metrics(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [{'name': 'shop'}, {'name': 'group'}, {'name': 'producer'},
                               {'name': 'supplier'}, {'name': 'product'}],
                'metrics': [],
                'date_range': ['2022-02-01', '2022-01-20'],
                'prev_date_range': ['2022-01-20', '2022-01-19']
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_nullable_date_range(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [{'name': 'shop'}, {'name': 'group'}, {'name': 'producer'},
                               {'name': 'supplier'}, {'name': 'product'}],
                'metrics': [{'name': 'turnover'}, {'name': 'sold_product_amount'}, {'name': 'turnover_diff_percent'},
                            {'name': 'income'}],
                'date_range': [],
                'prev_date_range': ['2022-01-20', '2022-01-19']
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_nullable_fields(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [],
                'metrics': [],
                'date_range': [],
                'prev_date_range': []
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_nullable_prev_date_range(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [{'name': 'shop'}, {'name': 'group'}, {'name': 'producer'},
                               {'name': 'supplier'}, {'name': 'product'}],
                'metrics': [{'name': 'turnover'}, {'name': 'sold_product_amount'}, {'name': 'turnover_diff_percent'},
                            {'name': 'income'}],
                'date_range': ['2022-01-20', '2022-01-19'],
                'prev_date_range': []
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_wrong_field_names(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dions': [{'name': 'shop'}, {'name': 'group'}, {'name': 'producer'},
                          {'name': 'supplier'}, {'name': 'product'}],
                'meics': [{'name': 'turnover'}, {'name': 'sold_product_amount'}, {'name': 'turnover_diff_percent'},
                          {'name': 'income'}],
                'date_range': ['2022-01-20', '2022-01-19'],
                'pv_date_range': []
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_incorrect_dimension_metric_name(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [{'name': 'shhop'}, {'name': 'gr_oup'}, {'name': 'pro""ducer'},
                               {'name': 'supplier'}, {'name': 'product'}],
                'metrics': [{'name': 'tuover'}, {'name': '__sold_product_amount'}, {'name': 'turnover_diff_pe"$"rcent'},
                            {'name': 'income'}],
                'date_range': ['2022-01-20', '2022-01-19'],
                'prev_date_range': []
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_nullable_prev_df(self):
        response = self.client.post(
            path='/analytics/',
            data={
                'dimensions': [{'name': 'shop'},
                               {'name': 'terminal',
                                'filtering': [{'field': 'id', 'value': [1, 2, 3, 4, 16, 18, 58, 60],
                                               'option': 'in'}]}],
                'metrics': [{'name': 'turnover'}, {'name': 'sold_product_amount'}, {'name': 'turnover_diff_percent'},
                            {'name': 'income'}, {'name': 'first_product_date'}, {'name': 'last_product_date'}],
                'date_range': ['2022-02-05', '2022-02-19'],
                'prev_date_range': ['2022-01-01', '2022-01-10']
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
