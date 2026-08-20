package com.safeye.backend.domain.alert.repository;

import com.safeye.backend.domain.alert.entity.AlertLog;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AlertLogRepository extends JpaRepository<AlertLog, UUID> {

}
