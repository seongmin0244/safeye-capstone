package com.safeye.backend.domain.zone.dto.request;

import jakarta.validation.constraints.NotBlank;

public record WorkZoneCreateRequest(
    @NotBlank(message = "구역명은 필수 입력값입니다.")
    String zoneName
) {

}
