from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import os
from practice import imageData
import json
import pydantic
from fastapi.responses import HTMLResponse
import shutil
import mimetypes
import base64


load_dotenv()

app = FastAPI()


class RequestModel(BaseModel):
    userId: str
    imageFormat: str
    imageData: str


@app.post("/")
def ocr():
    url = os.getenv("PASSPORT_INVOKE_URL")
    passport_request = RequestModel(
        userId="zypher", imageFormat="jpg", imageData=imageData  # base64
    )
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        url=url, headers=headers, data=passport_request.model_dump_json()
    )
    return response.json()


# 파일 업로드 디렉토리 설정
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


# 파일 업로드 엔드포인트
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # 파일 경로 설정
    file_location = os.path.join(UPLOAD_DIR, file.filename)

    # 파일 저장
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

        # 이미지 형식 인식
    image_format = file.filename.split(".")[-1].lower()
    mime_type, _ = mimetypes.guess_type(file.filename)

    print(image_format)
    print(mime_type, _)
    if mime_type and "image" in mime_type:
        # base64로 변환
        with open(file_location, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
        url = os.getenv("PASSPORT_INVOKE_URL")
        passport_request = RequestModel(
            userId="zypher", imageFormat=image_format, imageData=imageData  # base64
        )
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            url=url, headers=headers, data=passport_request.model_dump_json()
        )
        # OCR 응답 반환
        if response.status_code == 200:
            return {"filename": file.filename, "ocr_result": response.json()}
        else:
            return {
                "error": "Failed to get OCR result",
                "status_code": response.status_code,
            }

    else:
        return {"error": "Uploaded file is not a valid image"}


@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Upload</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .upload-container { margin-top: 20px; }
            input[type="file"] { padding: 10px; }
        </style>
    </head>
    <body>
        <h1>Upload an Image</h1>
        <div class="upload-container">
            <input type="file" id="fileInput" name="file" accept="image/*">
            <button onclick="uploadFile()">Upload</button>
            <p id="responseMessage"></p>
        </div>
    </body>
    <script>
        // DOMContentLoaded 이벤트를 사용하지 않고 함수 정의를 외부에 두고,
        // 페이지가 로드된 후 실행되도록 처리합니다.
        async function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const formData = new FormData();
            formData.append("file", fileInput.files[0]);

            const response = await fetch("/upload/", {
                method: "POST",
                body: formData
            });

            const data = await response.json();
            const messageElement = document.getElementById('responseMessage');

            // 기존 메시지 내용 지우기
            messageElement.textContent = "";

            if (response.ok) {
                messageElement.innerHTML = "File uploaded successfully: " + data.filename;
                messageElement.style.color = "green";
                
                // 줄바꿈을 위한 <br> 추가
                messageElement.innerHTML += "<br>";
                messageElement.innerHTML += "<br>";
                
                // OCR 결과를 표시
                if (data.ocr_result) {
                    messageElement.innerHTML += "OCR Result: ";
                    messageElement.innerHTML += "<br>";
                    messageElement.innerHTML += JSON.stringify(data.ocr_result,null, 3);

                }
            } else {
                messageElement.textContent = "Error uploading file.";
                messageElement.style.color = "red";
            }
        }
    </script>
    </html>
    """
    return HTMLResponse(content=html_content)


APPLICATION_PORT = 8888

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=APPLICATION_PORT, reload=True)
