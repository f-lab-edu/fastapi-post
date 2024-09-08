from locust import HttpUser, between, task

HOST = "http://127.0.0.1"


class WebsiteUser(HttpUser):
    host = HOST

    @task
    def test(self) -> None:
        with self.client.get("/", name="stress-test", catch_response=True) as response:
            None

    wait_time = between(1, 1)
