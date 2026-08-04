import { useState } from "react";

const MAX_SIZE_MB = 100;

function VideoUploadForm() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [fileError, setFileError] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setUploadStatus(null);

    if (!file) {
      setSelectedFile(null);
      setPreviewUrl(null);
      return;
    }

    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > MAX_SIZE_MB) {
      setFileError(
        `파일이 너무 큽니다 (${sizeMB.toFixed(1)}MB). ${MAX_SIZE_MB}MB 이하만 가능합니다.`,
      );
      setSelectedFile(null);
      setPreviewUrl(null);
      return;
    }

    setFileError(null);
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      console.log("영상을 먼저 선택해주세요");
      return;
    }

    const formData = new FormData();
    formData.append("video", selectedFile);

    setUploading(true);
    setUploadStatus(null);

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/upload-video`,
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
      <h2>영상 업로드</h2>
      <input type="file" accept="video/*" onChange={handleFileChange} />
      {selectedFile && (
        <p>
          선택된 파일: {selectedFile.name} (
          {(selectedFile.size / (1024 * 1024)).toFixed(1)}MB)
        </p>
      )}
      {fileError && <p style={{ color: "red" }}>{fileError}</p>}

      {previewUrl && (
        <div style={{ margin: "8px 0" }}>
          <video
            src={previewUrl}
            controls
            style={{ maxWidth: "400px", maxHeight: "300px", display: "block" }}
          />
        </div>
      )}
      <button type="submit" disabled={uploading || !selectedFile}>
        {uploading ? "업로드 중..." : "제출"}
      </button>

      {uploadStatus === "success" && (
        <p style={{ color: "green" }}>업로드 성공!</p>
      )}
      {uploadStatus === "error" && (
        <p style={{ color: "red" }}>업로드 실패. 다시 시도해보세요.</p>
      )}
    </form>
  );
}

export default VideoUploadForm;
