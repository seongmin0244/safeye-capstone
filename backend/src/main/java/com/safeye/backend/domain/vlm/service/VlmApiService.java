package com.safeye.backend.domain.vlm.service;

import com.safeye.backend.domain.vlm.dto.response.VlmResponseDto;
import com.safeye.backend.global.error.BusinessException;
import com.safeye.backend.global.error.GlobalErrorCode;
import io.netty.handler.timeout.ReadTimeoutException;
import io.netty.handler.timeout.WriteTimeoutException;
import java.io.IOException;
import java.net.ConnectException;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpStatusCode;
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

        .onStatus(HttpStatusCode::is4xxClientError, response -> {
          log.error("VLM 서버 클라이언트 에러 (4xx): {}", response.statusCode());
          return Mono.error(new BusinessException(GlobalErrorCode.VLM_SERVER_ERROR));
        })

        .onStatus(HttpStatusCode::is5xxServerError, response -> {
          log.error("VLM 서버 내부 에러 (5xx): {}", response.statusCode());
          return Mono.error(new BusinessException(GlobalErrorCode.VLM_SERVER_ERROR));
        })
        .bodyToMono(VlmResponseDto.class)

        .onErrorResume(WebClientRequestException.class, e -> {
          Throwable cause = e.getCause();

          if (cause instanceof ConnectException) {
            log.error("VLM 연결 실패: VLM 서버 다운 또는 네트워크 연결 거부 - cause: {}", cause.getMessage());
          } else if (cause instanceof ReadTimeoutException || cause instanceof WriteTimeoutException) {
            log.error("VLM 타임아웃: VLM 서버 연산 시간 초과 - cause: {}", cause.getMessage());
          } else {
            log.error("VLM 요청 실패: 기타 물리적 통신 오류 발생 - cause: {}", cause.getMessage());
          }
          return Mono.error(new BusinessException(GlobalErrorCode.VLM_SERVER_ERROR));
        })

        .block();
  }
}
