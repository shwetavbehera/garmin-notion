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

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yesterday = yesterday.strftime("%Y-%m-%d")

    sleep_data = api.get_sleep_data(yesterday)
    steps_data = api.get_steps_data(yesterday)

    sleep_hours = round((sleep_data.get("dailySleepDTO", {}).get("sleepTimeSeconds", 0) or 0) / 3600, 2)
    
    total_steps = 0
    for elem in steps_data:
        total_steps += elem.get("steps", 0)


    return {
        "date": yesterday,
        "sleep_hours": sleep_hours,
        "steps": total_steps
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
            "🚶🏾‍➡️ Steps": {"number": data["steps"]}
            
        }
    )
    print(f"Updated Notion for {data['date']}: {data['sleep_hours']}h sleep, {data['steps']} steps")

if __name__ == "__main__":
    api = init_garmin()
    data = get_yesterday_data(api)
    update_notion(data)
