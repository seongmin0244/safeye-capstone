package com.safeye.backend.domain.dangerevent.service;

import com.safeye.backend.domain.dangerevent.dto.request.DangerEventUploadRequest;
import com.safeye.backend.domain.dangerevent.dto.response.DangerEventDto;
import com.safeye.backend.domain.dangerevent.entity.DangerEvent;
import com.safeye.backend.domain.dangerevent.repository.DangerEventRepository;
import com.safeye.backend.domain.file.service.FileStorageService;
import com.safeye.backend.domain.vlm.dto.response.VlmResponseDto;
import com.safeye.backend.domain.vlm.service.VlmApiService;
import com.safeye.backend.domain.zone.entity.WorkZone;
import com.safeye.backend.domain.zone.service.WorkZoneService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class DangerEventService {

  private final DangerEventRepository dangerEventRepository;
  private final FileStorageService fileStorageService;
  private final WorkZoneService workZoneService;
  private final VlmApiService vlmApiService;

  @Transactional
  public DangerEventDto createDangerEvent(DangerEventUploadRequest request) {
    WorkZone workZone = workZoneService.getWorkZoneById(request.zoneId());

    String localFileUrl = fileStorageService.storeFile(request.file());

    VlmResponseDto vlmResponseDto = vlmApiService.analyzeFile(request.file());

    // 안전한 상황 isDanger = false 일 경우
    if (!vlmResponseDto.isDanger()) {
      log.info("정상 상황 감지. DB 적재 스킵 - isDanger: false");

      // TODO: 임시 응답 확인용 (추후 삭제)
      DangerEvent dangerEvent = DangerEvent.createDangerEvent(
          workZone,
          vlmResponseDto.severity(),
          localFileUrl,
          vlmResponseDto.vlmDescription(),
          vlmResponseDto.violatedRegulation(),
          vlmResponseDto.actionGuide(),
          null
      );
      return DangerEventDto.from(dangerEvent);
    }

    DangerEvent dangerEvent = DangerEvent.createDangerEvent(
        workZone,
        vlmResponseDto.severity(),
        localFileUrl,
        vlmResponseDto.vlmDescription(),
        vlmResponseDto.violatedRegulation(),
        vlmResponseDto.actionGuide(),
        null
    );

    dangerEventRepository.save(dangerEvent);

    log.info("위험 이벤트 저장 완료 - dangerEventId: {}", dangerEvent.getId());
    return DangerEventDto.from(dangerEvent);
  }
}
