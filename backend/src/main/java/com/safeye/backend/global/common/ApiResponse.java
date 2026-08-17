package com.safeye.backend.global.common;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.safeye.backend.global.error.ErrorCode;
import java.util.Map;

@JsonInclude(Include.NON_NULL)
public record ApiResponse<T>(
    boolean success,
    T data,
    ErrorDetail error
) {

  public static <T> ApiResponse<T> ok(T data) {
    return new ApiResponse<>(true, data, null);
  }

  public static <T> ApiResponse<T> ok() {
    return new ApiResponse<>(true, null, null);
  }

  public static <T> ApiResponse<T> fail(ErrorCode errorCode) {
    return new ApiResponse<>(false, null,
        new ErrorDetail(errorCode.getCode(), errorCode.getMessage(), null));
  }

  public static <T> ApiResponse<T> fail(ErrorCode errorCode, Map<String, Object> details) {
    return new ApiResponse<>(false, null,
        new ErrorDetail(errorCode.getCode(), errorCode.getMessage(), details));
  }

  @JsonInclude(Include.NON_NULL)
  public record ErrorDetail(
      String code,
      String message,

      @JsonInclude(Include.NON_EMPTY)
      Map<String, Object> details
  ) {

  }
}
