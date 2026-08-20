package com.safeye.backend.domain.vlm.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.safeye.backend.domain.dangerevent.entity.Severity;

public record VlmResponseDto(
    @JsonProperty("is_danger")
    boolean isDanger,

    Severity severity,

    @JsonProperty("vlm_description")
    String vlmDescription,

    @JsonProperty("violated_regulation")
    String violatedRegulation,

    @JsonProperty("action_guide")
    String actionGuide
) {

}
