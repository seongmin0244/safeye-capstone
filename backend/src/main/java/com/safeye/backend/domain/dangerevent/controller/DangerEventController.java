package com.safeye.backend.domain.dangerevent.controller;


import com.safeye.backend.domain.dangerevent.dto.request.DangerEventUploadRequest;
import com.safeye.backend.domain.dangerevent.dto.response.DangerEventDto;
import com.safeye.backend.domain.dangerevent.service.DangerEventService;
import com.safeye.backend.global.common.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/upload")
public class DangerEventController {

  private final DangerEventService dangerEventService;

  @PostMapping(value = "/file", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
  public ResponseEntity<ApiResponse<DangerEventDto>> uploadDangerEvent(
      @Valid @ModelAttribute DangerEventUploadRequest request
  ) {
    log.debug("[DangerEvent] 업로드 요청 수신 - zoneId: {}, fileName: {}", request.zoneId(), request.file().getOriginalFilename());

    DangerEventDto dangerEventDto = dangerEventService.createDangerEvent(request);

    return ResponseEntity.ok(ApiResponse.ok(dangerEventDto));
  }

}
