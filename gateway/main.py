from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from typing import Any
import jwt
from datetime import datetime, timedelta
import time
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(title="API Gateway", version="1.0.0")

SERVICES = {
    "student": "http://127.0.0.1:8001",
    "course": "http://127.0.0.1:8002",
}

JWT_SECRET = "CHANGE_THIS_SECRET"
JWT_ALG = "HS256"
security = HTTPBearer()


def create_access_token(payload: dict, minutes: int = 30) -> str:
    data = payload.copy()
    data["exp"] = datetime.utcnow() + timedelta(minutes=minutes)
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALG)


def verify_token(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = creds.credentials
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please login again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token. Please login again.")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            print(f"{request.method} {request.url.path} -> 500 ({duration_ms:.2f} ms) ERROR: {str(e)}")
            raise

        duration_ms = (time.time() - start) * 1000
        print(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f} ms)")
        return response


app.add_middleware(LoggingMiddleware)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


def safe_response_content(response: httpx.Response):
    if not response.text:
        return None
    try:
        return response.json()
    except ValueError:
        return {"message": response.text}


async def forward_request(service: str, path: str, method: str, **kwargs) -> Any:
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    url = f"{SERVICES[service]}{path}"
    timeout = httpx.Timeout(5.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if method == "GET":
                response = await client.get(url, **kwargs)
            elif method == "POST":
                response = await client.post(url, **kwargs)
            elif method == "PUT":
                response = await client.put(url, **kwargs)
            elif method == "DELETE":
                response = await client.delete(url, **kwargs)
            else:
                raise HTTPException(status_code=405, detail=f"Method '{method}' not allowed")

            return JSONResponse(
                content=safe_response_content(response),
                status_code=response.status_code
            )

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"{service} service is unavailable (connection failed). URL: {url}"
            )
        except httpx.ReadTimeout:
            raise HTTPException(
                status_code=504,
                detail=f"{service} service timeout (gateway waited too long). URL: {url}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"{service} service request error: {str(e)}. URL: {url}"
            )


@app.get("/")
def read_root():
    return {"message": "API Gateway is running", "available_services": list(SERVICES.keys())}


@app.post("/auth/login")
async def login(body: dict):
    username = body.get("username")
    password = body.get("password")

    if username == "admin" and password == "admin123":
        token = create_access_token({"sub": username}, minutes=30)
        return {"access_token": token, "token_type": "bearer"}

    raise HTTPException(status_code=401, detail="Invalid credentials")


# ------------------- Student Routes -------------------

@app.get("/gateway/students")
async def get_all_students(user=Depends(verify_token)):
    return await forward_request("student", "/api/students", "GET")


@app.get("/gateway/students/{student_id}")
async def get_student(student_id: int, user=Depends(verify_token)):
    return await forward_request("student", f"/api/students/{student_id}", "GET")


@app.post("/gateway/students")
async def create_student(payload: dict, user=Depends(verify_token)):
    return await forward_request("student", "/api/students", "POST", json=payload)


@app.put("/gateway/students/{student_id}")
async def update_student(student_id: int, payload: dict, user=Depends(verify_token)):
    return await forward_request("student", f"/api/students/{student_id}", "PUT", json=payload)


@app.delete("/gateway/students/{student_id}")
async def delete_student(student_id: int, user=Depends(verify_token)):
    return await forward_request("student", f"/api/students/{student_id}", "DELETE")


# ------------------- Course Routes -------------------

@app.get("/gateway/courses")
async def get_all_courses(user=Depends(verify_token)):
    return await forward_request("course", "/api/courses", "GET")


@app.get("/gateway/courses/{course_id}")
async def get_course(course_id: int, user=Depends(verify_token)):
    return await forward_request("course", f"/api/courses/{course_id}", "GET")


@app.post("/gateway/courses")
async def create_course(payload: dict, user=Depends(verify_token)):
    return await forward_request("course", "/api/courses", "POST", json=payload)


@app.put("/gateway/courses/{course_id}")
async def update_course(course_id: int, payload: dict, user=Depends(verify_token)):
    return await forward_request("course", f"/api/courses/{course_id}", "PUT", json=payload)


@app.delete("/gateway/courses/{course_id}")
async def delete_course(course_id: int, user=Depends(verify_token)):
    return await forward_request("course", f"/api/courses/{course_id}", "DELETE")