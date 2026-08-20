package com.safeye.backend.domain.zone.dto.response;

import com.safeye.backend.domain.zone.entity.WorkZone;
import java.util.UUID;

public record WorkZoneDto(
    UUID id,
    String zoneName
) {

  public static WorkZoneDto from(WorkZone zone) {
    return new WorkZoneDto(
        zone.getId(),
        zone.getZoneName()
    );
  }
}
