from typing import Optional

import uvicorn
from fastapi import FastAPI

app = FastAPI()

a = "dd"


@app.get("/")
def read_root():
    return {"Hello": "world"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}


if __name__ == "__main__":
    uvicorn.run(app, log_level="debug", reload=True)
