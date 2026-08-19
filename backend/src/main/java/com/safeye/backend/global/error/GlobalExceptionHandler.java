package com.safeye.backend.global.error;

import com.safeye.backend.global.common.ApiResponse;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import java.util.HashMap;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

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
