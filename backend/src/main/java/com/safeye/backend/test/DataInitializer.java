package com.safeye.backend.test;

import com.safeye.backend.domain.zone.entity.WorkZone;
import com.safeye.backend.domain.zone.repository.WorkZoneRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

// WorkZone 더미 데이터 초기화 코드
@Slf4j
@Component
@RequiredArgsConstructor
@Profile({"dev", "local", "test"})
public class DataInitializer implements CommandLineRunner {

  private final WorkZoneRepository workZoneRepository;

  @Override
  public void run(String... args) {
    // DB에 구역 데이터가 하나도 없을 때만 실행
    if (workZoneRepository.count() == 0) {
      log.info("가상 구역 마스터 데이터 초기화를 시작합니다...");

      WorkZone zone1 = workZoneRepository.save(WorkZone.createWorkZone("A동 타설구역"));
      WorkZone zone2 = workZoneRepository.save(WorkZone.createWorkZone("B동 자재창고"));
      WorkZone zone3 = workZoneRepository.save(WorkZone.createWorkZone("C동 용접구역"));

      log.info("초기화 완료. 테스트용 zoneId를 복사해서 포스트맨에 사용하세요.");
      log.info("[1] {} : {}", zone1.getZoneName(), zone1.getId());
      log.info("[2] {} : {}", zone2.getZoneName(), zone2.getId());
      log.info("[3] {} : {}", zone3.getZoneName(), zone3.getId());
    }
  }
}