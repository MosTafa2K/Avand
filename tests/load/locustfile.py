import os

from locust import HttpUser, between, task


class AvandUser(HttpUser):
    wait_time = between(0.2, 0.8)

    def on_start(self):
        self.booth_id = None
        self.order_token = os.getenv("LOCUST_ORDER_TOKEN")
        response = self.client.get(
            "/api/v1/booths?page=1&size=20&only_active=true",
            name="GET /api/v1/booths [bootstrap]",
        )
        if response.ok:
            items = response.json().get("items", [])
            if items:
                self.booth_id = items[0]["id"]

    @task(4)
    def get_products(self):
        self.client.get(
            "/api/v1/products?page=1&size=20",
            name="GET /api/v1/products [baseline]",
        )

    @task(2)
    def search_products(self):
        self.client.get(
            "/api/v1/products?page=1&size=20&search=%D8%B9%D8%B3%D9%84",
            name="GET /api/v1/products [text-search]",
        )

    @task(2)
    def filter_products(self):
        self.client.get(
            "/api/v1/products?page=1&size=20&min_price=100&max_price=1000000"
            "&min_rating=3&city=%D8%AA%D9%87%D8%B1%D8%A7%D9%86",
            name="GET /api/v1/products [price-rating-city-filters]",
        )

    @task(1)
    def sort_products_by_price(self):
        self.client.get(
            "/api/v1/products?page=1&size=20&sort_by=price&sort_order=asc",
            name="GET /api/v1/products [sort-price]",
        )

    @task(1)
    def sort_products_by_sales(self):
        self.client.get(
            "/api/v1/products?page=1&size=20&sort_by=sales&sort_order=desc",
            name="GET /api/v1/products [sort-sales]",
        )

    @task(2)
    def get_booths(self):
        self.client.get(
            "/api/v1/booths?page=1&size=20&only_active=true",
            name="GET /api/v1/booths [list]",
        )

    @task(2)
    def get_booth_products(self):
        if self.booth_id:
            self.client.get(
                f"/api/v1/booths/{self.booth_id}/products?page=1&size=20",
                name="GET /api/v1/booths/{booth_id}/products",
            )

    @task(1)
    def get_orders_by_product(self):
        headers = {"Authorization": f"Bearer {self.order_token}"} if self.order_token else {}
        with self.client.get(
            "/api/v1/orders?page=1&size=20&product_search=%D8%B9%D8%B3%D9%84",
            headers=headers,
            name="GET /api/v1/orders [product-search]",
            catch_response=True,
        ) as response:
            if not self.order_token and response.status_code == 401:
                response.success()
