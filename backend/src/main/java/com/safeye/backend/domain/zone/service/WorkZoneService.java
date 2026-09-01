package com.safeye.backend.domain.zone.service;

import com.safeye.backend.domain.zone.dto.request.WorkZoneCreateRequest;
import com.safeye.backend.domain.zone.dto.response.WorkZoneDto;
import com.safeye.backend.domain.zone.entity.WorkZone;
import com.safeye.backend.domain.zone.exception.WorkZoneErrorCode;
import com.safeye.backend.domain.zone.repository.WorkZoneRepository;
import com.safeye.backend.global.error.BusinessException;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Sort;
import org.springframework.data.domain.Sort.Direction;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class WorkZoneService {
  // work_zones를 시스템 관리자가 미리 세팅하는 데이터로 취급

  private final WorkZoneRepository workZoneRepository;

  @Transactional
  public WorkZoneDto createWorkZone(WorkZoneCreateRequest request) {
    log.debug("신규 구역 생성 시도 - zoneName: {}", request.zoneName());
    String zoneName = request.zoneName();

    if (workZoneRepository.existsByZoneName(zoneName)) {
      log.warn("구역 생성 실패 - 중복된 zoneName: {}", zoneName);
      throw new BusinessException(WorkZoneErrorCode.DUPLICATE_ZONE_NAME, Map.of("zoneName", zoneName));
    }

    WorkZone workZone = WorkZone.createWorkZone(zoneName);
    workZone = workZoneRepository.save(workZone);

    log.info("신규 구역 생성 완료 - zoneId: {}, zoneName: {}", workZone.getId(), zoneName);
    return WorkZoneDto.from(workZone);
  }

  public List<WorkZoneDto> getAllWorkZones() {
    // 가나다순(오름차순) 정렬
    return workZoneRepository.findAll(Sort.by(Direction.ASC, "zoneName"))
        .stream()
        .map(WorkZoneDto::from)
        .toList();
  }

  public WorkZone getWorkZoneById(UUID zoneId) {
    return workZoneRepository.findById(zoneId)
        .orElseThrow(() -> new BusinessException(WorkZoneErrorCode.ZONE_NOT_FOUND, Map.of("zoneId", zoneId)));
  }
}