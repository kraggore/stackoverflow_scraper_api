# API for StackOverflow_Scraper
# Author: MEYLAN ERIC 2024-02-01
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from cachetools import TTLCache
from Scraper import Scraper as Scr

app = FastAPI()
cache = TTLCache(maxsize=1000, ttl=60)
scr = Scr()


def jsonify_data(data):
    json_compatible_item_data = jsonable_encoder(data)
    data = JSONResponse(content=json_compatible_item_data)
    return data


@app.get("/tag/{tag}")
async def get_subject(tag: str):
    tag = scr.remove_illegal_chars(tag)
    if tag in cache:
        return cache[tag]
    data = scr.get_questions(f'/tagged/{tag}?tab=Votes')
    data = jsonify_data(data)
    cache[tag] = data
    return data


@app.get("/question/most_voted")
async def get_most_voted():
    if 'most_voted' in cache:
        return cache['most_voted']
    data = scr.get_questions('/tab=Votes')
    data = jsonify_data(data)
    cache['most_voted'] = data
    return data


@app.get("/question/{q_id}")
async def get_question(q_id: str):
    if q_id in cache:
        return cache[q_id]
    data = scr.get_answers(q_id)
    data = jsonify_data(data)
    cache[q_id] = data
    return data


@app.get("/cache")
async def get_cache():
    return jsonify_data(cache)
