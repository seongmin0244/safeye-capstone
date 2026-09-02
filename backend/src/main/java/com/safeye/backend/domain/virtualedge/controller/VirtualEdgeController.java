package com.safeye.backend.domain.virtualedge.controller;

import com.safeye.backend.domain.virtualedge.service.VirtualEdgeSimulator;
import com.safeye.backend.global.common.ApiResponse;
import java.time.Duration;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/virtual-edge")
@RequiredArgsConstructor
public class VirtualEdgeController {

  private final VirtualEdgeSimulator virtualEdgeSimulator;

  @Value("${app.simulator.push-rate:6000}")
  private long pushRateMs;

  @PostMapping("/start")
  public ResponseEntity<ApiResponse<String>> startSimulator() {
    virtualEdgeSimulator.start();

    long pushRateSeconds = pushRateMs / 1000;

    return ResponseEntity.ok(ApiResponse.ok("가상 엣지 시뮬레이터 가동 (" + pushRateSeconds + "초 주기)"));
  }

  @PostMapping("/stop")
  public ResponseEntity<ApiResponse<String>> stopSimulator() {
    virtualEdgeSimulator.stop();
    return ResponseEntity.ok(ApiResponse.ok("가상 엣지 시뮬레이터 중단"));
  }

}
