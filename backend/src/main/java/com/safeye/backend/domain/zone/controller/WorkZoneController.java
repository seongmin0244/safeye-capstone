package com.safeye.backend.domain.zone.controller;

import com.safeye.backend.domain.zone.dto.request.WorkZoneCreateRequest;
import com.safeye.backend.domain.zone.dto.response.WorkZoneDto;
import com.safeye.backend.domain.zone.service.WorkZoneService;
import com.safeye.backend.global.common.ApiResponse;
import jakarta.validation.Valid;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/zones")
public class WorkZoneController {

  private final WorkZoneService workZoneService;

  @PostMapping
  public ResponseEntity<ApiResponse<WorkZoneDto>> createWorkZone(
      @Valid @RequestBody WorkZoneCreateRequest request
  ) {
    WorkZoneDto response = workZoneService.createWorkZone(request);
    return ResponseEntity.ok(ApiResponse.ok(response));
  }

  @GetMapping
  public ResponseEntity<ApiResponse<List<WorkZoneDto>>> getAllWorkZones() {
    List<WorkZoneDto> response = workZoneService.getAllWorkZones();
    return ResponseEntity.ok(ApiResponse.ok(response));
  }
}
