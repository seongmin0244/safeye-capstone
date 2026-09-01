package com.safeye.backend.domain.zone.entity;

import com.safeye.backend.global.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "work_zones")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class WorkZone extends BaseEntity {

  @Column(nullable = false, length = 100)
  private String zoneName;

  private WorkZone(String zoneName) {
    this.zoneName = zoneName;
  }

  public static WorkZone createWorkZone(String zoneName) {
    return new WorkZone(zoneName);
  }
}
