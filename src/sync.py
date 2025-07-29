import os
import datetime
from garminconnect import Garmin
from notion_client import Client

def init_garmin():


    email = os.getenv("GARMIN_USERNAME")
    password = os.getenv("GARMIN_PASSWORD")
    token_store = os.path.expanduser("~/.garminconnect")

    try:
        garmin = Garmin()
        garmin.login(token_store)
    except:
        garmin = Garmin(email=email, password=password)
        garmin.login()
        garmin.garth.dump(token_store)

    return garmin

def get_yesterday_data(api):

    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    sleep_data = api.get_sleep_data(yesterday)
    steps_data = api.get_steps_data(yesterday)

    try:
        sleep_hours = round(sleep_data.get("dailySleepDTO", {}).get("sleepTimeSeconds", 0) / 3600, 2)
    except:
        sleep_hours = 0
    
    try:
        total_steps = sum(elem.get("steps", 0) for elem in steps_data)
    except:
        total_steps = 0

    activities = api.get_activities_by_date(yesterday, yesterday)

    gym = False
    run = False
    for activity in activities:
        if activity.get("activityType").get("typeKey") == "strength_training":
            gym = True
        if activity.get("activityType").get("typeKey") == "running":
            run = True

    return {
        "date": yesterday,
        "sleep_hours": sleep_hours,
        "steps": total_steps,
        "gym": gym,
        "run": run
    }

def update_notion(data):


    notion = Client(auth=os.getenv("NOTION_TOKEN"))
    db_id = os.getenv("NOTION_DATABASE_ID")

    # Query for yesterday's page
    response = notion.databases.query(
        **{
            "database_id": db_id,
            "filter": {
                "property": "📅 Date",
                "date": {"equals": data["date"]}
            }
        }
    )

    if not response["results"]:
        print(f"No Notion page found for {data['date']}")
        return

    page_id = response["results"][0]["id"]

    notion.pages.update(
        page_id=page_id,
        properties={
            "😴 Sleep (hrs)": {"number": data["sleep_hours"]},
            "🚶🏾‍➡️ Steps": {"number": data["steps"]},
            "💪🏾 Gym": {"checkbox": data["gym"]},
            "👟 Run": {"checkbox": data["run"]},
            
        }
    )
    print(f"Updated Notion for {data['date']}: {data['sleep_hours']}h sleep, {data['steps']} steps")

if __name__ == "__main__":
    api = init_garmin()
    data = get_yesterday_data(api)
    update_notion(data)
