from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from command_hub.pipeline import ARKPipeline

app=FastAPI()
pipeline=ARKPipeline()

class RequestModel(BaseModel): 
    request:str

@app.post("/process")
async def process_request(req:RequestModel):
    try: 
        return {"result":pipeline.run(req.request)}
    except Exception as e: 
        raise HTTPException(status_code=400,detail=str(e))
