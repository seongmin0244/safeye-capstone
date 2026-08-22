package com.safeye.backend.domain.zone.repository;

import com.safeye.backend.domain.zone.entity.WorkZone;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface WorkZoneRepository extends JpaRepository<WorkZone, UUID> {

  boolean existsByZoneName(String zoneName);
}
