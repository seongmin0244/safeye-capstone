package com.safeye.backend.domain.zone.service;

import com.safeye.backend.domain.zone.entity.WorkZone;
import com.safeye.backend.domain.zone.exception.WorkZoneErrorCode;
import com.safeye.backend.domain.zone.repository.WorkZoneRepository;
import com.safeye.backend.global.error.BusinessException;
import java.util.Map;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class WorkZoneService {
  // work_zones를 시스템 관리자가 미리 세팅하는 데이터로 취급

  private final WorkZoneRepository workZoneRepository;

  public WorkZone getWorkZoneById(UUID zoneId) {
    return workZoneRepository.findById(zoneId)
        .orElseThrow(() -> new BusinessException(WorkZoneErrorCode.ZONE_NOT_FOUND, Map.of("zoneId", zoneId)));
  }
}