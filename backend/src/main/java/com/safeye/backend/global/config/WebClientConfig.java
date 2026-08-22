package com.safeye.backend.global.config;

import io.netty.channel.ChannelOption;
import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

@Configuration
public class WebClientConfig {

  @Value("${vlm.server.url}")
  private String vlmServerUrl;

  @Value("${vlm.server.timeout}")
  private long vlmTimeout;

  @Bean
  public WebClient vlmWebClient() {
    HttpClient httpClient = HttpClient.create()
        .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 5000) // VLM 서버와 연결하는 데 5초 이상 걸리면 실패
        .responseTimeout(Duration.ofSeconds(vlmTimeout)); // 연결 후 VLM 서버가 30초 내에 응답을 안 주면 실패

    return WebClient.builder()
        .baseUrl(vlmServerUrl)
        .clientConnector(new ReactorClientHttpConnector(httpClient))
        .build();
  }
}
