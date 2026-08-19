package com.safeye.backend.domain.dangerevent.dto.request;

import jakarta.validation.constraints.NotNull;
import java.util.UUID;
import org.springframework.web.multipart.MultipartFile;

public record DangerEventUploadRequest(

    @NotNull(message = "이미지/영상 파일은 필수입니다.")
    MultipartFile file,

    @NotNull(message = "구역 ID은 필수입니다.")
    UUID zoneId

    // 추후 String cctvId 추가
) {

}
