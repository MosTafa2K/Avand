from locust import HttpUser, between, task


class AvandUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_products(self):
        self.client.get("/api/v1/products")

    @task(2)
    def get_booths(self):
        self.client.get("/api/v1/booths")

    @task(1)
    def check_service_ready(self):
        self.client.get("/api/v1/ready")
