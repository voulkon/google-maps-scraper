from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from pymongo import MongoClient
from botasaurus_api import Api
from time import sleep
import os

mongo_conn_string = os.getenv("MONGO_CONN_STRING", "mongodb://localhost:27017/")
mongo_db = os.getenv("MONGO_DB_NAME","gmaps-scrapper-test")

the_mongo_db = MongoClient(mongo_conn_string)[mongo_db]
api = Api()
scrapping_api = FastAPI()

# Pydantic model for request data validation
class TaskData(BaseModel):
    queries: List[str] = Field(default=['Web Developers in Bangalore'], description="List of queries to search")
    country: Optional[str] = Field(default=None, description="Country to focus the search on")
    business_type: str = Field(default="", description="Type of business to search for")
    max_cities: Optional[int] = Field(default=None, description="Maximum number of cities to include in the search")
    randomize_cities: bool = Field(default=True, description="Whether to randomize cities in the search")
    api_key: str = Field(default="", description="API key for authentication")
    enable_reviews_extraction: bool = Field(default=True, description="Whether to enable reviews extraction")
    max_reviews: Optional[int] = Field(default=None, description="Maximum number of reviews to extract")
    reviews_sort: str = Field(default="newest", description="Sorting order for reviews")
    lang: Optional[str] = Field(default=None, description="Language for the search results")
    max_results: Optional[int] = Field(default=None, description="Maximum number of results to return")
    coordinates: str = Field(default="", description="Coordinates to focus the search on")
    zoom_level: int = Field(default=14, description="Zoom level for the map search")

def is_task_finished(task_ids: List[int]):
    this_runs_task_ids = task_ids.copy()
    while this_runs_task_ids:
        for t, task_id in enumerate(this_runs_task_ids):
            init_resp = api.get_task(task_id)
            is_task_finished = init_resp['status'] == 'completed'
            if is_task_finished:
                this_runs_task_ids.pop(t)
            sleep(2)
    return True

def upload_results(the_mongo_db, a_task_complete, user_requested_it:str):
    key_of_all_stuff = 'result'
    task_info = a_task_complete.pop(key_of_all_stuff)
    
    a_task_complete['user_requested_it'] = user_requested_it
    
    the_mongo_db['result_related_stuff'].insert_one(a_task_complete)
    for place in task_info:
        featured_reviews = place.pop('featured_reviews')
        detailed_reviews = place.pop('detailed_reviews')
        
        place['user_requested_it'] = user_requested_it
        the_mongo_db['place_related'].insert_one(place)
        for detailed_review in detailed_reviews:
            detailed_review['user_requested_it'] = user_requested_it
            the_mongo_db['reviews'].insert_one(detailed_review)

@scrapping_api.get("/")
def say_hi():
    return {'hi': 'there'}

@scrapping_api.post("/send_a_task")
def post_a_task(
    query: str
    user_requested_it:str
):
    data_to_be = {
        'queries': [query],
        'country': None,
        'business_type': '',
        'max_cities': None,
        'randomize_cities': True,
        'api_key': '',
        'enable_reviews_extraction': True,
        'max_reviews': 20,
        'reviews_sort': 'newest',
        'lang': None,
        'max_results': None,
        'coordinates': '',
        'zoom_level': 14,
    }
    try:
        a_task = api.create_async_task(data=data_to_be, scraper_name='google_maps_scraper')
        this_tasks_ids: List[int] = [task['id'] for task in a_task if task['task_name'] == 'All Task']
        if is_task_finished(this_tasks_ids):
            result_of_scraping = api.get_task(this_tasks_ids[0])
            upload_results(the_mongo_db, a_task_complete=result_of_scraping, user_requested_it = user_requested_it)
        return {"task_id": this_tasks_ids[0], "status": "Task uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@scrapping_api.get("/what_about_this_task/{task_id}")
def learn_about_a_task(task_id: int):
    return {"to be": "developed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(scrapping_api, host="0.0.0.0", port=8765)
