package com.safeye.backend.global.error;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
@AllArgsConstructor
public enum GlobalErrorCode implements ErrorCode {

  // [CMM] 공통 에러
  INVALID_INPUT_VALUE(HttpStatus.BAD_REQUEST, "CMM-001", "잘못된 입력값입니다."),
  INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "CMM-002", "서버 내부 오류가 발생했습니다."),

  // [EVT] 위험 감지(DangerEvent) 에러
  EVENT_NOT_FOUND(HttpStatus.NOT_FOUND, "EVT-001", "해당 위험 이벤트를 찾을 수 없습니다."),

  // [VLM] AI 통신 에러
  VLM_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "VLM-001", "AI 분석 서버와 통신 중 오류가 발생했습니다.");

  private final HttpStatus status;
  private final String code;
  private final String message;
}
