package com.safeye.backend.global.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {

  @Value("${vlm.server.url}")
  private String vlmServerUrl;

  @Bean
  public WebClient vlmWebClient() {
    return WebClient.builder()
        .baseUrl(vlmServerUrl)
        // TODO: 추후 Connection Timeout, Read Timeout 설정 추가
        .build();
  }
}
