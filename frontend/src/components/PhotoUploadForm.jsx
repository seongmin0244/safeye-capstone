import { useState, useRef } from "react";
import { DEV_ZONE_ID, UPLOAD_ENDPOINT } from "../constants/config";

function PhotoUploadForm() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // "success" | "error" | null

  const fileInputRef = useRef(null);

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
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("zoneId", DEV_ZONE_ID);

    setUploading(true);
    setUploadStatus(null);

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}${UPLOAD_ENDPOINT}`,
        {
          method: "POST",
          body: formData,
        },
      );
      const json = await response.json();

      if(!response.ok || !json.success) {
        throw new Error(json.error?.message ?? "업로드 실패");
      }

      const data = json.data;
      console.log("분석 결과:", data);
      setUploadStatus("success");

    } catch (error) {
      console.error("전송 실패:", error);
      setUploadStatus("error");
    } finally {
      setUploading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white border border-border rounded-[14px] p-6 max-w-[420px]"
    >
      <h2 className="text-[14.5px] font-bold mb-4">이미지 업로드</h2>

      <input
        type="file"
        accept=".jpg, .jpeg, .png, .webp"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />

      <div
        onClick={() => fileInputRef.current.click()}
        className="border-2 border-dashed border-border rounded-[10px] p-8 flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-accent hover:bg-accent-bg transition-colors"
      >
        {previewUrl ? (
          <img
            src={previewUrl}
            alt="미리보기"
            className="max-w-full max-h-[220px] block rounded-[8px]"
          />
        ) : (
          <>
            <span className="text-sm font-semibold text-ink">
              클릭하여 이미지 선택
            </span>
            <span className="text-xs text-muted">JPG, PNG 파일 업로드</span>
          </>
        )}
      </div>

      {selectedFile && (
        <p className="text-sm text-muted mb-2">
          선택된 파일: {selectedFile.name}
        </p>
      )}

      <button
        type="submit"
        disabled={uploading}
        className="w-full mt-4 py-3.5 rounded-[10px] bg-accent text-white text-sm font-bold disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {uploading ? "업로드 중..." : "제출"}
      </button>

      {uploadStatus === "success" && (
        <p className="text-safe text-sm font-semibold mt-2">업로드 성공</p>
      )}
      {uploadStatus === "error" && (
        <p className="text-danger text-sm font-semibold mt-2">
          업로드 실패. 다시 시도해주세요.
        </p>
      )}
    </form>
  );
}

export default PhotoUploadForm;
