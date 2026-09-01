package com.safeye.backend.global.error;

import com.safeye.backend.domain.file.exception.FileErrorCode;
import com.safeye.backend.global.common.ApiResponse;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import java.util.HashMap;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.multipart.MultipartException;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

  // 직접 정의한 비즈니스 예외
  @ExceptionHandler(BusinessException.class)
  public ResponseEntity<ApiResponse<Void>> handleBusinessException(BusinessException e) {
    ErrorCode errorCode = e.getErrorCode();
    log.warn("[CustomException] Type: {}, Code: {}, Message: {}, Details: {}", e.getClass().getSimpleName(), errorCode.getCode(), e.getMessage(), e.getDetails());
    return ResponseEntity
        .status(errorCode.getStatus())
        .body(ApiResponse.fail(errorCode, e.getDetails()));
  }

  // @Valid 검증 실패 - 요청 Body의 DTO 필드 검증 실패
  @ExceptionHandler(MethodArgumentNotValidException.class)
  public ResponseEntity<ApiResponse<Void>> handleValidationException(MethodArgumentNotValidException e) {
    Map<String, Object> validationDetails = new HashMap<>();

    for (FieldError fieldError : e.getBindingResult().getFieldErrors()) {
      validationDetails.put(fieldError.getField(), fieldError.getDefaultMessage());
    }
    log.warn("[MethodArgumentNotValidException] Details: {}", validationDetails);
    GlobalErrorCode errorCode = GlobalErrorCode.INVALID_INPUT_VALUE;
    return ResponseEntity
        .status(errorCode.getStatus())
        .body(ApiResponse.fail(errorCode, validationDetails));
  }

  // @Valid 검증 실패 - 쿼리 파라미터나 PathVariable 검증 실패
  @ExceptionHandler(ConstraintViolationException.class)
  public ResponseEntity<ApiResponse<Void>> handleConstraintViolation(ConstraintViolationException e) {
    Map<String, Object> validationDetails = new HashMap<>();

    for (ConstraintViolation<?> violation : e.getConstraintViolations()) {
      String path = violation.getPropertyPath().toString();
      String field = path.substring(path.lastIndexOf('.') + 1);
      validationDetails.put(field, violation.getMessage());
    }
    log.warn("[ConstraintViolationException] Details: {}", validationDetails);
    GlobalErrorCode errorCode = GlobalErrorCode.INVALID_INPUT_VALUE;
    return ResponseEntity
        .status(errorCode.getStatus())
        .body(ApiResponse.fail(errorCode, validationDetails));
  }

  @ExceptionHandler(MultipartException.class)
  public ResponseEntity<ApiResponse<Void>> handleMultipartException(MultipartException e) {
    // 글로벌 용량 제한에 걸린 경우
    if (e instanceof MaxUploadSizeExceededException) {
      log.warn("[MaxUploadSizeExceededException] 글로벌 파일 용량 제한 초과: {}", e.getMessage());
      FileErrorCode errorCode = FileErrorCode.FILE_SIZE_EXCEEDED;
      return ResponseEntity
          .status(HttpStatus.BAD_REQUEST)
          .body(ApiResponse.fail(errorCode));
    }

    // 파일명 인코딩 헤더 크기 초과 등 잘못된 요청일 경우
    log.warn("[MultipartException] 파일 파싱 실패 (파일명이 너무 길거나 깨짐): {}", e.getMessage());
    GlobalErrorCode errorCode = GlobalErrorCode.INVALID_INPUT_VALUE;
    return ResponseEntity
        .status(HttpStatus.BAD_REQUEST)
        .body(ApiResponse.fail(errorCode));
  }

  // 예상치 못한 에러
  @ExceptionHandler(Exception.class)
  public ResponseEntity<ApiResponse<Void>> handleException(Exception e) {
    log.error("[UncaughtException] Message: {}", e.getMessage(), e);
    GlobalErrorCode errorCode = GlobalErrorCode.INTERNAL_SERVER_ERROR;
    return ResponseEntity
        .status(errorCode.getStatus())
        .body(ApiResponse.fail(errorCode));
  }


}
