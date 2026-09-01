package com.safeye.backend.domain.file.exception;

import com.safeye.backend.global.error.ErrorCode;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;

@Getter
@RequiredArgsConstructor
public enum FileErrorCode implements ErrorCode {

  EMPTY_FILE_UPLOADED(HttpStatus.BAD_REQUEST, "FILE-001", "업로드된 파일이 비어있거나 존재하지 않습니다."),
  FILE_UPLOAD_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "FILE-002", "로컬 파일 업로드 중 오류가 발생했습니다."),
  INVALID_FILE_EXTENSION(HttpStatus.BAD_REQUEST, "FILE-003", "지원하지 않는 파일 형식(확장자 또는 MIME 타입)입니다."),
  FILE_SIZE_EXCEEDED(HttpStatus.BAD_REQUEST, "FILE-004", "업로드 가능한 최대 파일 크기를 초과했습니다.")
  ;

  private final HttpStatus status;
  private final String code;
  private final String message;
}
