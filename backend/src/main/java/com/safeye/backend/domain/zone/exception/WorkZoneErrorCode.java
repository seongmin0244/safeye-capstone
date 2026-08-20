package com.safeye.backend.domain.zone.exception;

import com.safeye.backend.global.error.ErrorCode;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;

@Getter
@RequiredArgsConstructor
public enum WorkZoneErrorCode implements ErrorCode {

  ZONE_NOT_FOUND(HttpStatus.NOT_FOUND, "ZONE-001", "해당 구역을 찾을 수 없습니다."),
  DUPLICATE_ZONE_NAME(HttpStatus.CONFLICT, "ZONE-002", "이미 존재하는 구역 이름입니다.")
  ;

  private final HttpStatus status;
  private final String code;
  private final String message;
}
