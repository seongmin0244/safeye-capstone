package com.safeye.backend.global.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.servers.Server;
import java.util.List;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

@Configuration
@Profile({"dev", "local"})
public class SwaggerConfig {

  @Bean
  public OpenAPI openAPI() {
    // API 기본 정보 설정
    Info info = new Info()
        .title("SAFEye 관제 시스템 API 명세서")
        .description("VLM 기반 산업 현장 위험 상황 맥락 이해 및 RAG 안전 관제 백엔드 API 문서입니다.")
        .version("v1.0.0");

    // 서버 URL 설정 (로컬 개발 환경)
    Server localServer = new Server()
        .url("http://localhost:8080")
        .description("로컬 개발 서버 (dev)");

    return new OpenAPI()
        .info(info)
        .servers(List.of(localServer))
        .components(new Components());
  }
}
