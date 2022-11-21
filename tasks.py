import asyncio
import os
import aiohttp as aiohttp
import config

from celery import Celery, chord

celery_app = Celery("worker",
                    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
                    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"))

celery_app.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
celery_app.conf.task_routes = {"tasks.*": "main-queue"}
celery_app.conf.result_expires = 300
celery_app.conf.update(task_track_started=True)

celery_app.conf.broker_transport_options = {
    "retry_policy": {
        "timeout": 5.0
    }
}
celery_app.conf.result_backend_transport_options = {
    "retry_policy": {
        "timeout": 5.0
    }
}


def create_serp_scraping_task_group(keywords_data: list):
    payloads = []
    for keyword in keywords_data:
        for page_num in range(1, config.SERP_PAGES + 1):
            payloads.append({
                "source": f"{config.SERP_TARGET}",
                "domain": f"{config.SERP_DOMAIN}",
                "query": f"{keyword}",
                "start_page": page_num,
                "pages": 1,
                "parse": config.SERP_PARSE_RESULT,
                "context": [
                    {"key": "results_language", "value": f"{config.SERP_LANGUAGE}"},
                ],
            })
    tasks = chord(
        (scraping_task.s(
            payload, {"username": f"{config.OXY_SERPS_AUTH_USERNAME}",
                      "pass": f"{config.OXY_SERPS_AUTH_PASSWORD}"}) for payload in payloads)
    )(aggregate_scraping_results_task.s())
    return tasks.get()


async def _aiohttp_request_helper_oxy_json_post(request_target: str,
                                                json_payload: dict,
                                                credentials: dict,
                                                return_type: str = "json"):
    aiohttp_config = {
        "connector": aiohttp.TCPConnector(verify_ssl=False),
        "timeout": aiohttp.ClientTimeout(total=60 * 3 * 3),
    }
    async with aiohttp.ClientSession(**aiohttp_config) as session:
        async with session.post(
                request_target,
                json=json_payload,
                auth=aiohttp.BasicAuth(f"{credentials['username']}", f"{credentials['pass']}"),
                timeout=500) as resp:
            try:
                if resp.status == 401:
                    raise Exception("Incorrect Credentials. Account doesn't exist")
                if return_type == "json":
                    return await resp.json()
                return await resp.text()
            except KeyError as e:
                raise Exception(
                    f"GET {request_target} You've ran out of API request limits or API field "
                    f"is empty or invalid.: {str(e)}")
            except Exception as e:
                raise Exception(f"GET {request_target} returned unexpected response "
                                f"code: {str(e)}")


@celery_app.task(acks_late=True,
                 bind=True,
                 autoretry_for=(Exception,),
                 soft_time_limit=35,
                 retry_kwargs={"max_retries": 3, "countdown": 2})
def scraping_task(self, payload: dict, credentials: dict):
    url = "https://realtime.oxylabs.io/v1/queries"
    data = asyncio.run(_aiohttp_request_helper_oxy_json_post(url, payload, credentials))
    if data and data["results"]:
        return_data = []
        for result in data["results"]:
            try:
                organic_data = result["content"]["results"]["organic"]
                if organic_data:
                    for url in organic_data:
                        return_data.append({
                            "keyword": payload["query"],
                            "page_number": payload["start_page"],
                            "position": url["pos"],
                            "url": url["url"],
                            "title": url["title"],
                        })
            except Exception as e:
                print(str(e))
            except KeyError as e:
                raise e
        return {"data": return_data, "status": "success"}
    return {"data": [], "status": "error"}


@celery_app.task(acks_late=True,
                 bind=True,
                 autoretry_for=(Exception,),
                 retry_kwargs={"max_retries": 3, "countdown": 2})
def aggregate_scraping_results_task(self, results: list):
    scraper_task_results = []
    for result in results:
        if result["status"] == "success":
            scraper_task_results.extend(result["data"])
    return {"results": scraper_task_results, "task_id": self.request.id}
