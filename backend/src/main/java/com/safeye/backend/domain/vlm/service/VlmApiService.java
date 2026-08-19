package com.safeye.backend.domain.vlm.service;

import com.safeye.backend.domain.vlm.dto.response.VlmResponseDto;
import com.safeye.backend.global.error.BusinessException;
import com.safeye.backend.global.error.GlobalErrorCode;
import java.io.IOException;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import reactor.core.publisher.Mono;


@Slf4j
@Service
@RequiredArgsConstructor
public class VlmApiService {

  private final WebClient vlmWebClient;

  public VlmResponseDto analyzeFile(MultipartFile file) {
    log.info("VLM 서버로 파일 분석 요청 시작 - 파일명: {}", file.getOriginalFilename());

    MultipartBodyBuilder bodyBuilder = new MultipartBodyBuilder();

    try {
      // MultipartFile을 WebClient가 이해할 수 있는 ByteArrayResource로 변환
      ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
        @Override
        public String getFilename() {
          // 원본 파일명을 헤더에 강제 주입
          return file.getOriginalFilename();
        }
      };

      bodyBuilder.part("image", fileResource, MediaType.parseMediaType(file.getContentType()));

      // 강제 에러 테스트: 500번대 에러
      //bodyBuilder.part("mock_made", "error");

      // 응답 지연 무시: 목 서버의 랜덤 대기 시간 무시
      bodyBuilder.part("delay", 0);

    } catch (IOException e) {
      log.error("VLM 요청용 바이트 변환 중 I/O 오류 발생", e);
      throw new BusinessException(GlobalErrorCode.INTERNAL_SERVER_ERROR, Map.of("filename", file.getOriginalFilename()));
    }

    // webClient 비동기 POST 요청 발송
    return vlmWebClient.post()
        .uri("/v1/analyze")
        .contentType(MediaType.MULTIPART_FORM_DATA)
        .body(BodyInserters.fromMultipartData(bodyBuilder.build()))
        .retrieve()

        .onStatus(status -> status.is4xxClientError(), response -> {
          log.error("VLM 서버 클라이언트 에러 (4xx): {}", response.statusCode());
          return Mono.error(new BusinessException(GlobalErrorCode.VLM_SERVER_ERROR));
        })

        .onStatus(status -> status.is5xxServerError(), response -> {
          log.error("VLM 서버 내부 에러 (5xx): {}", response.statusCode());
          return Mono.error(new BusinessException(GlobalErrorCode.VLM_SERVER_ERROR));
        })
        .bodyToMono(VlmResponseDto.class)

        .onErrorResume(WebClientRequestException.class, e -> {
          log.error("VLM 서버 물리적 연결 실패 (네트워크/서버다운): {}", e.getMessage());
          return Mono.error(new BusinessException(GlobalErrorCode.VLM_SERVER_ERROR));
        })

        .block();
  }
}
