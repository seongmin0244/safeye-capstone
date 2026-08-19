package com.safeye.backend.domain.file.service;

import com.safeye.backend.domain.file.exception.FileErrorCode;
import com.safeye.backend.global.error.BusinessException;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Slf4j
@Service
public class LocalFileStorageService implements FileStorageService {

  private static final String BASE_UPLOAD_DIR = "uploads/";

  // 허용할 이미지 규격
  private static final List<String> ALLOWED_IMAGE_MIMES = List.of("image/jpeg", "image/png",
      "image/webp");
  private static final List<String> ALLOWED_IMAGE_EXTS = List.of("jpg", "jpeg", "png", "webp");

  // 허용할 영상 규격
  private static final List<String> ALLOWED_VIDEO_MIMES = List.of("video/mp4", "video/x-msvideo",
      "video/quicktime");
  private static final List<String> ALLOWED_VIDEO_EXTS = List.of("mp4", "avi", "mov");


  @Override
  public String storeFile(MultipartFile file) {
    if (file == null || file.isEmpty()) {
      log.warn("파일 업로드 실패 - 파일이 비어있음");
      throw new BusinessException(FileErrorCode.EMPTY_FILE_UPLOADED);
    }

    String fileType = validateAndGetFileType(file);

    String originalFilename = file.getOriginalFilename();
    String extension = originalFilename.substring(originalFilename.lastIndexOf(".") + 1)
        .toLowerCase();

    String subDir = fileType.equals("image") ? "images/" : "videos/";
    String targetDir = BASE_UPLOAD_DIR + subDir;

    String filename = UUID.randomUUID() + "." + extension;

    File dir = new File(targetDir);
    if (!dir.exists()) {
      dir.mkdirs();
    }

    try {
      Path filePath = Paths.get(targetDir, filename);
      Files.write(filePath, file.getBytes());

      String fileUrl = "http://localhost:8080/uploads/" + subDir + filename;
      log.info("로컬 파일 저장 완료 - type: {}, url: {}", fileType, fileUrl);

      return fileUrl;
    } catch (IOException e) {
      log.error("파일 업로드 중 I/O 오류 발생", e);
      throw new BusinessException(FileErrorCode.FILE_UPLOAD_FAILED,
          Map.of("filename", originalFilename != null ? originalFilename : "unknown"));
    }
  }

  // 파일의 MIME Type과 확장자를 이중 검증하고, image인지 video인지 반환
  private String validateAndGetFileType(MultipartFile file) {
    String contentType = file.getContentType();
    String originalFilename = file.getOriginalFilename();

    if (originalFilename == null || !originalFilename.contains(".")) {
      log.warn("업로드 실패 - 확장자가 없는 파일명: {}", originalFilename);
      throw new BusinessException(FileErrorCode.INVALID_FILE_EXTENSION,
          Map.of("filename", originalFilename));
    }

    String extension = originalFilename.substring(originalFilename.lastIndexOf(".") + 1)
        .toLowerCase();

    if (contentType != null && ALLOWED_IMAGE_MIMES.contains(contentType.toLowerCase())
        && ALLOWED_IMAGE_EXTS.contains(extension)) {
      return "image";
    }

    if (contentType != null && ALLOWED_VIDEO_MIMES.contains(contentType.toLowerCase())
        && ALLOWED_VIDEO_EXTS.contains(extension)) {
      return "video";
    }

    log.warn("업로드 실패 - 허용되지 않은 파일 규격. contentType: {}, extension: {}", contentType, extension);
    throw new BusinessException(FileErrorCode.INVALID_FILE_EXTENSION,
        Map.of("contentType", contentType != null ? contentType : "null", "extension", extension));
  }
}
