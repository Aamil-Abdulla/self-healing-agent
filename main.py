import uvicorn
from graph import app as agent
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
app = FastAPI()

class HealRequest(BaseModel):
    original_code: str
    task_description: str

@app.get("/")
async def home():
    with open("index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.post("/heal")
async def heal_code(request: HealRequest):
    result = agent.invoke({
        "original_code": request.original_code,
        "task_description": request.task_description,
        "current_code": request.original_code,
        "attempts": [],
        "attempts_count": 0,
        "success": False,
        "explanation": "",
        "analysis": ""
    })
    return result
    
    

if __name__ == "__main__":
    uvicorn.run(app,host="0.0.0.0", port=8000)
    