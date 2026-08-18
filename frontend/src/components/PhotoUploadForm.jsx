import { useState } from "react";

function PhotoUploadForm() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // "success" | "error" | null

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file);
    setUploadStatus(null);

    if (file) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
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

      {previewUrl && (
        <div style={{ margin: "8px 0" }}>
          <img
            src={previewUrl}
            alt="미리보기"
            style={{ maxWidth: "300px", maxHeight: "300px", display: "block" }}
          />
        </div>
      )}

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

export default PhotoUploadForm;
