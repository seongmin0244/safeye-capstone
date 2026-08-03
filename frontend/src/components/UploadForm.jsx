// 컴포넌트: 그냥 화면 조각을 반환하는 함수
// <input type="file" accept="image/*" />
// 위 문장은 파일 선택 버튼이며, image 파일만으로 제한함
// handleFileChange: 파일 선택 버튼에서 파일을 고르는 순간 실행
// e.target.files[0]: 선택한 파일 정보, 배열 형태로 올 때 첫번째 것만 선택
// setSelectedFile(file): 이 파일 정보를 state에 저장 (이 순간 화면 자동으로 다시 그려짐)
// handleSubmit: 제출 버튼을 눌렀을 때 실행
// new FormData(): 파일을 담는 상자 (일반 JSON 파일 X, 전송 전용 형식)
// formData.append("image", selectedFile): 상자에 "image"라고 이름을 붙여서 파일을 넣음 (API 계약의 key=image와 이름이 일치해야 함)
// fetch(...): 서버에 요청을 보내는 함수, Spring Boot 백엔드가 쓰는 포트 주소
// method: "POST": 보내는 방식을 뜻함
// body: formData: 파일 상자를 요청에 담아보냄
// async/await: 서버 응답이 올 때까지 기다렸다가 다음 코드를 실행하라는 뜻
// try/catch: 서버가 꺼져있거나 네트워크 문제가 있을 때 에러를 잡음
// onChange={handleFileChange}: input 태그에 값이 바뀌면 handleFileChange 실행
// {selectedFile && <p> ...}: selectedFile이 있다면 뒤의 문장을 실행시킴
// export default ... : 다른 파일에서 해당 컴포넌트를 가져다 쓸 수 있도록 해줌

import { useState } from "react";

function UploadForm() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // "success" | "error" | null

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file);
    setUploadStatus(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      console.log("파일을 선택해주세요");
      return;
    }

    const formData = new FormData();
    formData.append("image", selectedFile);

    setUploading(true);
    setUploadStatus(null);

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/upload`,
        {
          method: "POST",
          body: formData,
        },
      );
      const result = await response.json();
      console.log("서버 응답:", result);
      setUploadStatus("success");
    } catch (error) {
      console.error("전송 실패:", error);
      setUploadStatus("error");
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>이미지 업로드</h2>
      <input type="file" accept="image/*" onChange={handleFileChange} />
      {selectedFile && <p>선택된 파일: {selectedFile.name}</p>}

      <button type="submit" disabled={uploading}>
        {uploading ? "업로드 중..." : "제출"}
      </button>

      {uploadStatus === "success" && (
        <p style={{ color: "green" }}>업로드 성공</p>
      )}
      {uploadStatus === "error" && (
        <p style={{ color: "red" }}>업로드 실패. 다시 시도해주세요.</p>
      )}
    </form>
  );
}

export default UploadForm;
