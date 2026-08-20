package com.safeye.backend.domain.alert.entity;

import com.safeye.backend.domain.dangerevent.entity.DangerEvent;
import com.safeye.backend.global.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "alert_log")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class AlertLog extends BaseEntity {

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "event_id", nullable = false)
  private DangerEvent dangerEvent;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 20)
  private AlertType alertType;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false, length = 20)
  private AlertStatus status;

  private AlertLog(DangerEvent dangerEvent, AlertType alertType, AlertStatus status) {
    this.dangerEvent = dangerEvent;
    this.alertType = alertType;
    this.status = status;
  }

  public static AlertLog createAlertLog(DangerEvent dangerEvent, AlertType alertType, AlertStatus status) {
    return new AlertLog(dangerEvent, alertType, status);
  }

}
