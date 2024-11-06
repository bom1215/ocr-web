from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import os
import json
import pydantic
from fastapi.responses import HTMLResponse
import shutil
import mimetypes
import base64
import uvicorn


load_dotenv()

app = FastAPI()


class RequestModel(BaseModel):
    userId: str
    imageFormat: str
    imageData: str


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):

        # 이미지 형식 인식
    image_format = file.filename.split(".")[-1].lower()
    mime_type, _ = mimetypes.guess_type(file.filename)

    print(image_format)
    print(mime_type, _)
    if mime_type and "image" in mime_type:
        # base64로 변환
        image_data = base64.b64encode(await file.read()).decode("utf-8")
        url = os.getenv("PASSPORT_INVOKE_URL")
        passport_request = RequestModel(
            userId="zypher", imageFormat=image_format, imageData=image_data  # base64
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
            <button onclick="uploadFile()">OCR Start</button>
            <p id="responseMessage"></p>
        </div>
    </body>
    <script>
    async function uploadFile() {
        const fileInput = document.getElementById('fileInput');
        const uploadButton = document.querySelector('button');  // "OCR Start" 버튼
        const messageElement = document.getElementById('responseMessage');

        // 버튼 비활성화
        uploadButton.disabled = true;

        // "추출 중" 메시지 표시
        messageElement.innerHTML = "추출 중... 잠시만 기다려 주세요.";
        messageElement.style.color = "blue";

        // 파일이 선택되지 않았을 경우 처리
        if (!fileInput.files.length) {
            messageElement.textContent = "No file selected.";
            messageElement.style.color = "red";
            uploadButton.disabled = false;  // 오류가 발생하면 버튼을 다시 활성화
            return;
        }

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        try {
            const response = await fetch("/upload/", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            // 기존 메시지 내용 지우기
            messageElement.innerHTML = "";

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
                    messageElement.innerHTML += JSON.stringify(data.ocr_result, null, 3);
                }
            } else {
                messageElement.textContent = "Error uploading file.";
                messageElement.style.color = "red";
            }
        } catch (error) {
            messageElement.textContent = "Error occurred during the upload.";
            messageElement.style.color = "red";
        } finally {
            // 요청 완료 후 버튼 다시 활성화
            uploadButton.disabled = false;
            }
        }
    </script>
    </html>
    """
    return HTMLResponse(content=html_content)


APPLICATION_PORT = 8888

if __name__ == "__main__":

    uvicorn.run("main:app", host="127.0.0.1", port=APPLICATION_PORT, reload=True)
