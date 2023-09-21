import httpx  # requests capability, but can work with async
from prefect import flow, task, get_run_logger, serve
from prefect.artifacts import create_markdown_artifact
from prefect.tasks import task_input_hash


@task
def fetch_weather(lat: float, lon: float):
    base_url = "https://api.open-meteo.com/v1/forecast/"
    weather = httpx.get(
        base_url,
        params=dict(latitude=lat, longitude=lon, hourly="temperature_2m"),
    )
    most_recent_temp = float(weather.json()["hourly"]["temperature_2m"][0])
    return most_recent_temp


@task
def save_weather(temp: float):
    logger = get_run_logger()
    logger.info(f"Saving temp: {temp}")
    create_markdown_artifact(f"""
Weather info
============
| *Most recent temp* |
| ------------------ |
| {temp}            |
""", "weather-info", "A table of weather info")
    with open("weather.csv", "w+") as w:
        w.write(str(temp))
    return "Successfully wrote temp"


@flow
def pipeline(lat: float, lon: float):
    temp = fetch_weather(lat, lon)
    result = save_weather(temp)
    return result

@task
def fetch_cat_fact():
    return httpx.get("https://catfact.ninja/fact?max_length=140").json()["fact"]


@task(persist_result=True)
def formatting(fact: str):
    return fact.title()

@flow
def pipeline2(message: str):
    print(message)
    cat_fact = fetch_cat_fact()
    formatted_title = formatting(cat_fact)
    create_markdown_artifact(f"""
Cat Fact
========
{formatted_title}
""")


if __name__ == "__main__":
    # pipeline.serve(name="its_a_flow")
    serve(pipeline, pipeline2)
