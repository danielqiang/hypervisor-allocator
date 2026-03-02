import asyncio

from fastapi import FastAPI, status, Depends
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from structlog import get_logger

from src.allocator.engine import (
    HypervisorAllocator,
    InsufficientResourcesError,
    DropletAlreadyProvisioned,
    UnknownDropletIDError,
)
from src.helpers.util import get_hosts_fpath, load_config

app = FastAPI()
logger = get_logger()

_allocator = HypervisorAllocator(load_config(get_hosts_fpath())["hosts"])


def get_allocator():
    return _allocator


app.state.write_mutex = asyncio.Lock()


@app.exception_handler(RuntimeError)
async def generic_exception_handler(request: Request, exc: RuntimeError):
    logger.error(
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Unknown Error", "details": str(exc)},
    )


@app.exception_handler(InsufficientResourcesError)
async def insufficient_resources_exception_handler(
    request: Request, exc: InsufficientResourcesError
):
    logger.error(
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=200,
        content={"error": "Insufficient Resources", "details": str(exc)},
    )


@app.exception_handler(DropletAlreadyProvisioned)
async def droplet_already_provisioned_exception_handler(
    request: Request, exc: DropletAlreadyProvisioned
):
    logger.error(
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=403,
        content={"error": "Droplet Already Provisioned", "details": str(exc)},
    )


@app.exception_handler(UnknownDropletIDError)
async def unknown_droplet_id_exception_handler(
    request: Request, exc: UnknownDropletIDError
):
    logger.error(
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=403,
        content={"error": "Unknown Droplet ID", "details": str(exc)},
    )


class Droplet(BaseModel):
    id: str
    cpu_required: float
    ram_required: float
    anti_affinity_group: str = None


@app.post("/provision/", status_code=status.HTTP_201_CREATED)
async def provision(droplet: Droplet, allocator=Depends(get_allocator)):
    async with app.state.write_mutex:
        host_id = allocator.provision(
            droplet.id, droplet.cpu_required, droplet.ram_required, droplet.anti_affinity_group
        )

    return {"status": "success", "host_id": host_id}


@app.delete("/droplet/{droplet_id}")
async def deprovision(droplet_id: str, allocator=Depends(get_allocator)):
    async with app.state.write_mutex:
        allocator.deprovision(droplet_id)


@app.get("/stats/")
async def stats(allocator=Depends(get_allocator)):
    stats = allocator.stats()

    return {
        "status": "success",
        "stats": f"CPU used: {stats[0] * 100}%, RAM used: {stats[1] * 100}%",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("service:app", host="127.0.0.1", port=8000, reload=True)
